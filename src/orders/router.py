from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.orders.models import OrderModel, OrderItemModel, OrderStatus
from src.orders.schemas import (
    OrderCreate,
    OrderResponse,
    OrderPaginatedResponse,
    OrderCreateResponse,
    OrderStatusUpdate,
)
from src.movies.models import MovieModel
from src.accounts.models import UserModel
from src.dependencies import get_current_user, get_current_admin_user
from src.orders.services import send_order_confirmation_email

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
    payload: OrderCreate,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Place a new order, automatically excluding unavailable, already purchased, or pending movies."""
    requested_ids = list(set(payload.movie_ids))

    # 1. Fetch available movies from database
    movies_query = await db.execute(select(MovieModel).where(MovieModel.id.in_(requested_ids)))
    movies = list(movies_query.scalars().all())

    found_ids = {m.id for m in movies}
    missing_ids = set(requested_ids) - found_ids

    # 2. Exclude movies already purchased by the user in paid orders
    purchased_query = await db.execute(
        select(OrderItemModel.movie_id)
        .join(OrderModel)
        .where(
            and_(
                OrderModel.user_id == current_user.id,
                OrderModel.status == OrderStatus.PAID,
                OrderItemModel.movie_id.in_(found_ids),
            )
        )
    )
    already_purchased_ids = set(purchased_query.scalars().all())

    # Filter out unavailable and already purchased movies
    excluded_ids = list(missing_ids | already_purchased_ids)
    valid_movies = [m for m in movies if m.id not in already_purchased_ids]

    # 3. Check for existing pending orders containing the same movies (avoid duplicates)
    pending_query = await db.execute(
        select(OrderItemModel.movie_id)
        .join(OrderModel)
        .where(
            and_(
                OrderModel.user_id == current_user.id,
                OrderModel.status == OrderStatus.PENDING,
                OrderItemModel.movie_id.in_(found_ids),
            )
        )
    )
    pending_movie_ids = set(pending_query.scalars().all())

    # Add pending movies to excluded IDs for notification
    excluded_ids.extend(list(pending_movie_ids - set(excluded_ids)))

    # Filter out movies that are already in pending orders
    valid_movies = [m for m in valid_movies if m.id not in pending_movie_ids]

    if not valid_movies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No valid movies to order. All requested movies are either unavailable, already purchased, or already in your pending orders."
        )

    # Calculate total amount based on current valid prices
    total_amount = sum((m.price for m in valid_movies), start=Decimal("0.00"))

    new_order = OrderModel(
        user_id=current_user.id,
        total_amount=total_amount,
        status=OrderStatus.PENDING,
    )
    db.add(new_order)
    await db.flush()

    for movie in valid_movies:
        db.add(
            OrderItemModel(
                order_id=new_order.id,
                movie_id=movie.id,
                price_at_order=movie.price,
            )
        )

    await db.commit()

    order_res = await db.execute(
        select(OrderModel)
        .options(selectinload(OrderModel.items))
        .where(OrderModel.id == new_order.id)
    )
    order = order_res.scalar_one()

    notification_msg = None
    if excluded_ids:
        notification_msg = "Some movies were excluded from your order because they were unavailable, already purchased, or already in a pending order."

    return {
        "order": order,
        "excluded_movie_ids": excluded_ids,
        "notification": notification_msg,
    }


@router.get("/my", response_model=List[OrderResponse])
async def list_user_orders(
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Retrieve all orders placed by the current user."""
    query = (
        select(OrderModel)
        .options(selectinload(OrderModel.items))
        .where(OrderModel.user_id == current_user.id)
        .order_by(OrderModel.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()


@router.post("/{order_id}/cancel", response_model=OrderResponse)
async def cancel_order(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Cancel a pending order before payment."""
    order = (
        await db.execute(
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(and_(OrderModel.id == order_id, OrderModel.user_id == current_user.id))
        )
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.PENDING:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot cancel order with status '{order.status}'. Only pending orders can be canceled."
        )

    order.status = OrderStatus.CANCELED
    await db.commit()
    await db.refresh(order)
    return order


@router.post("/{order_id}/pay", response_model=OrderResponse)
async def pay_order(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Finalize payment for a pending order, revalidate prices, and send email confirmation."""
    order = (
        await db.execute(
            select(OrderModel)
            .options(selectinload(OrderModel.items).selectinload(OrderItemModel.movie))
            .where(and_(OrderModel.id == order_id, OrderModel.user_id == current_user.id))
        )
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.PENDING:
        raise HTTPException(status_code=400, detail="Order is not in pending status")

    recalculated_total = Decimal("0.00")
    for item in order.items:
        if not item.movie:
            raise HTTPException(
                status_code=400,
                detail=f"Movie with ID {item.movie_id} is no longer available."
            )
        recalculated_total += item.movie.price
        item.price_at_order = item.movie.price

    order.total_amount = recalculated_total
    order.status = OrderStatus.PAID
    await db.commit()
    await db.refresh(order)

    # Trigger async email notification
    await send_order_confirmation_email(
        user_email=current_user.email,
        order_uuid=order.uuid,
        total_amount=float(order.total_amount),
    )

    return order


@router.post("/{order_id}/refund-request", response_model=OrderResponse)
async def request_refund(
    order_id: int,
    current_user: UserModel = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Request a refund for a successfully paid order."""
    order = (
        await db.execute(
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(and_(OrderModel.id == order_id, OrderModel.user_id == current_user.id))
        )
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status != OrderStatus.PAID:
        raise HTTPException(
            status_code=400,
            detail="Refund can only be requested for successfully paid orders."
        )

    order.status = OrderStatus.REFUND_REQUESTED
    await db.commit()
    await db.refresh(order)
    return order


@router.get("/admin/all", response_model=OrderPaginatedResponse)
async def admin_list_orders(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    user_id: Optional[int] = Query(None, description="Filter by user ID"),
    order_status: Optional[OrderStatus] = Query(None, description="Filter by status"),
    date_from: Optional[datetime] = Query(None, description="Filter from creation date"),
    date_to: Optional[datetime] = Query(None, description="Filter up to creation date"),
    current_admin: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint to view and filter all user orders."""
    query = select(OrderModel).options(selectinload(OrderModel.items))

    if user_id:
        query = query.where(OrderModel.user_id == user_id)
    if order_status:
        query = query.where(OrderModel.status == order_status)
    if date_from:
        query = query.where(OrderModel.created_at >= date_from)
    if date_to:
        query = query.where(OrderModel.created_at <= date_to)

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar_one()

    offset = (page - 1) * size
    query = query.order_by(OrderModel.created_at.desc()).offset(offset).limit(size)

    items = (await db.execute(query)).scalars().all()

    return {
        "total": total,
        "page": page,
        "size": size,
        "items": items,
    }


@router.patch("/admin/{order_id}/status", response_model=OrderResponse)
async def admin_update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    current_admin: UserModel = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin endpoint to manually update an order status (e.g., process a refund)."""
    order = (
        await db.execute(
            select(OrderModel)
            .options(selectinload(OrderModel.items))
            .where(OrderModel.id == order_id)
        )
    ).scalar_one_or_none()

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    order.status = payload.status
    await db.commit()
    await db.refresh(order)
    return order

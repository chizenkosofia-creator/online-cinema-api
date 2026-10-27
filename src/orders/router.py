from decimal import Decimal
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.database import get_db
from src.orders.models import OrderModel, OrderItemModel
from src.orders.schemas import OrderCreate, OrderResponse
from src.movies.models import MovieModel
from src.accounts.models import User

from src.dependencies import get_current_user

router = APIRouter(prefix="/orders", tags=["Orders"])


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
async def create_order(
        payload: OrderCreate,
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(MovieModel).where(MovieModel.id.in_(payload.movie_ids)))
    movies = result.scalars().all()

    if not movies:
        raise HTTPException(status_code=404, detail="No movies found with the provided IDs")

    found_movie_ids = {movie.id for movie in movies}
    missing_ids = set(payload.movie_ids) - found_movie_ids
    if missing_ids:
        raise HTTPException(status_code=400, detail=f"Movies with IDs {list(missing_ids)} not found")

    total_amount = sum((movie.price for movie in movies), start=Decimal("0.00"))

    new_order = OrderModel(
        user_id=current_user.id,
        total_amount=total_amount,
        status="completed",
    )
    db.add(new_order)
    await db.flush()

    order_items = []
    for movie in movies:
        item = OrderItemModel(
            order_id=new_order.id,
            movie_id=movie.id,
            price=movie.price,
        )
        order_items.append(item)
        db.add(item)

    await db.commit()

    order_query = (
        select(OrderModel)
        .options(selectinload(OrderModel.items))
        .where(OrderModel.id == new_order.id)
    )
    created_order = (await db.execute(order_query)).scalar_one()
    return created_order


@router.get("/", response_model=List[OrderResponse])
async def list_user_orders(
        current_user: User = Depends(get_current_user),
        db: AsyncSession = Depends(get_db),
):
    query = (
        select(OrderModel)
        .options(selectinload(OrderModel.items))
        .where(OrderModel.user_id == current_user.id)
        .order_by(OrderModel.created_at.desc())
    )
    result = await db.execute(query)
    return result.scalars().all()

from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from src.orders.models import OrderStatus


class OrderItemResponse(BaseModel):
    id: int
    movie_id: int
    price_at_order: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    movie_ids: List[int] = Field(..., min_length=1, description="List of movie IDs to order")


class OrderResponse(BaseModel):
    id: int
    uuid: str
    user_id: int
    total_amount: Decimal
    status: OrderStatus
    created_at: datetime
    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


class OrderPaginatedResponse(BaseModel):
    total: int
    page: int
    size: int
    items: List[OrderResponse]


class OrderCreateResponse(BaseModel):
    order: OrderResponse
    excluded_movie_ids: List[int] = Field(
        default=[], description="Movies excluded because they were already purchased or unavailable"
    )
    notification: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus = Field(..., description="New status for the order")

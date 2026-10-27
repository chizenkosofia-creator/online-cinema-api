from datetime import datetime
from decimal import Decimal
from typing import List
from pydantic import BaseModel, ConfigDict, Field


class OrderItemResponse(BaseModel):
    id: int
    movie_id: int
    price: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    movie_ids: List[int] = Field(..., min_length=1, description="List of movie IDs to purchase")


class OrderResponse(BaseModel):
    id: int
    uuid: str
    total_amount: Decimal
    status: str
    created_at: datetime
    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)

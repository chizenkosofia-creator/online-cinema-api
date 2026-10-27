import uuid
from datetime import datetime
from decimal import Decimal
from typing import List
from sqlalchemy import String, DECIMAL, ForeignKey, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.movies.models import MovieModel

from src.database import Base


class OrderModel(Base):
    __tablename__ = "orders"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    uuid: Mapped[str] = mapped_column(
        String(36), unique=True, nullable=False, default=lambda: str(uuid.uuid4())
    )
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    total_amount: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False, default=0.00)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="completed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    items: Mapped[List["OrderItemModel"]] = relationship(
        "OrderItemModel", back_populates="order", cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<Order(id={self.id}, total_amount={self.total_amount}, status='{self.status}')>"


class OrderItemModel(Base):
    __tablename__ = "order_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    movie_id: Mapped[int] = mapped_column(ForeignKey("movies.id", ondelete="RESTRICT"), nullable=False)
    price: Mapped[Decimal] = mapped_column(DECIMAL(10, 2), nullable=False)

    order: Mapped["OrderModel"] = relationship("OrderModel", back_populates="items")
    movie: Mapped["MovieModel"] = relationship("MovieModel")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, movie_id={self.movie_id}, price={self.price})>"

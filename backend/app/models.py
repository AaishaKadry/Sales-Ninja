from sqlalchemy import String, Integer, Float, Date, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from .database import Base

class Sale(Base):
    __tablename__ = "sales"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    order_id: Mapped[str] = mapped_column(String(80), unique=True, index=True)
    order_date: Mapped[object] = mapped_column(Date, index=True)
    customer: Mapped[str] = mapped_column(String(160), default="Unknown")
    product: Mapped[str] = mapped_column(String(160), index=True)
    category: Mapped[str] = mapped_column(String(100), default="Uncategorized")
    region: Mapped[str] = mapped_column(String(100), default="Unknown")
    quantity: Mapped[int] = mapped_column(Integer, default=1)
    unit_price: Mapped[float] = mapped_column(Float, default=0)
    unit_cost: Mapped[float] = mapped_column(Float, default=0)
    created_at: Mapped[object] = mapped_column(DateTime(timezone=True), server_default=func.now())

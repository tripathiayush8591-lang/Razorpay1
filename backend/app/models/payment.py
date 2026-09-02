from datetime import datetime
from typing import Optional
from sqlalchemy import String, Boolean, Text, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class PaymentAttempt(Base):
    __tablename__ = "payment_attempts"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    merchant_order_id: Mapped[str] = mapped_column(String(36), ForeignKey("merchant_orders.id"), nullable=False, index=True)
    razorpay_order_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    signature_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    raw_event_reference: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    merchant_order = relationship("MerchantOrder", back_populates="payment_attempts")

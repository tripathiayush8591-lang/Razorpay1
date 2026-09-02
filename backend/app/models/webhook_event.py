from datetime import datetime
from typing import Optional
from sqlalchemy import String, Text, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class ProcessedWebhookEvent(Base):
    __tablename__ = "processed_webhook_events"

    event_id: Mapped[str] = mapped_column(String(255), primary_key=True)
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    razorpay_order_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    razorpay_payment_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True, index=True)
    processed_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    payload_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

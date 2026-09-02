from datetime import datetime
from sqlalchemy import String, Integer, Text, Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class MerchantPolicy(Base):
    __tablename__ = "merchant_policies"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    merchant_id: Mapped[str] = mapped_column(String(36), ForeignKey("merchants.id"), unique=True, nullable=False)
    max_discount_percent: Mapped[int] = mapped_column(Integer, default=15, nullable=False)
    allow_out_of_stock: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    require_purchase_approval: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    cross_sell_rules_json: Mapped[str] = mapped_column(Text, nullable=False, default="[]")
    delivery_rules_json: Mapped[str] = mapped_column(Text, nullable=False, default="{}")
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    merchant = relationship("Merchant", back_populates="policies")

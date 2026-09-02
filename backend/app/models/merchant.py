from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class Merchant(Base):
    __tablename__ = "merchants"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)

    admin_users = relationship("AdminUser", back_populates="merchant", cascade="all, delete-orphan")
    products = relationship("Product", back_populates="merchant", cascade="all, delete-orphan")
    policies = relationship("MerchantPolicy", back_populates="merchant", uselist=False, cascade="all, delete-orphan")
    carts = relationship("Cart", back_populates="merchant", cascade="all, delete-orphan")
    orders = relationship("MerchantOrder", back_populates="merchant", cascade="all, delete-orphan")

import enum
from datetime import datetime, timezone
from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class TransactionStatus(str, enum.Enum):
    pending = "pending"
    paid = "paid"
    canceled = "canceled"
    failed = "failed"


class Transaction(Base):
    __tablename__ = "transactions"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(64), nullable=False)
    plan_key: Mapped[str] = mapped_column(String(64), nullable=False)
    plan_title: Mapped[str] = mapped_column(String(255), nullable=False)
    duration_days: Mapped[int] = mapped_column(Integer, nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # stored in minimal units (kopecks or satoshi-like)
    payment_method: Mapped[str | None] = mapped_column(String(64), nullable=True)
    status: Mapped[TransactionStatus] = mapped_column(
        Enum(TransactionStatus), default=TransactionStatus.pending, nullable=False
    )
    # Idempotency key prevents double-processing the same checkout
    idempotency_key: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    paid_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    user: Mapped["User"] = relationship(back_populates="transactions")  # noqa: F821

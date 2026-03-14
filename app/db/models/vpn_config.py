import enum
from datetime import datetime, timezone
from sqlalchemy import DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.base import Base


class VpnConfigStatus(str, enum.Enum):
    active = "active"
    expired = "expired"
    revoked = "revoked"


class VpnConfig(Base):
    __tablename__ = "vpn_configs"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False, index=True)
    country_code: Mapped[str] = mapped_column(String(64), nullable=False)
    config_value: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[VpnConfigStatus] = mapped_column(
        Enum(VpnConfigStatus), default=VpnConfigStatus.active, nullable=False
    )
    purchased_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship(back_populates="vpn_configs")  # noqa: F821

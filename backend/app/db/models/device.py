from datetime import datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class DeviceStatus(StrEnum):
    """Possible lifecycle states of a GlasHaus device."""

    ACTIVE = "active"
    REVOKED = "revoked"
    PENDING_REACTIVATION = "pending_reactivation"


class Device(Base):
    """Represent a registered GlasHaus device."""

    __tablename__ = "devices"

    device_id: Mapped[UUID] = mapped_column(primary_key=True)
    device_name: Mapped[str] = mapped_column(String(255))
    device_status: Mapped[DeviceStatus] = mapped_column(
        String(32),
        default=DeviceStatus.ACTIVE,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
    )
    last_seen_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    revoked_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

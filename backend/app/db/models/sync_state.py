from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models.base import Base


class SyncStatus(StrEnum):
    """Possible synchronization states for a device."""

    IDLE = "idle"
    SYNCING = "syncing"
    ERROR = "error"
    RESYNC_REQUIRED = "resync_required"


class SyncState(Base):
    """Persist synchronization state for one device."""

    __tablename__ = "sync_states"

    device_id: Mapped[UUID] = mapped_column(
        ForeignKey("devices.device_id"),
        primary_key=True,
    )
    cursor: Mapped[int] = mapped_column(default=0)
    next_local_sequence: Mapped[int] = mapped_column(default=1)
    sync_status: Mapped[SyncStatus] = mapped_column(
        String(32),
        default=SyncStatus.IDLE,
    )
    last_sync_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_sync_completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_sync_error: Mapped[str | None] = mapped_column(
        String(2000),
        nullable=True,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
    )

from datetime import UTC, datetime

from app.core.ids import new_local_id
from app.db.database import get_session, initialize_database
from app.db.models import Base, Device, DeviceStatus, SyncState, SyncStatus
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker


def test_device_and_sync_state_survive_session_restart() -> None:
    """Persist a device and its sync state across database sessions."""
    engine = create_engine("sqlite:///:memory:")

    try:
        Base.metadata.create_all(bind=engine)

        device_id = new_local_id()
        created_at = datetime.now(UTC)

        with Session(engine) as session:
            device = Device(
                device_id=device_id,
                device_name="Test Device",
                device_status=DeviceStatus.ACTIVE,
                created_at=created_at,
            )
            sync_state = SyncState(device_id=device_id)

            session.add(device)
            session.add(sync_state)
            session.commit()

        with Session(engine) as session:
            stored_device = session.get(Device, device_id)
            stored_sync_state = session.get(SyncState, device_id)

            assert stored_device is not None
            assert stored_sync_state is not None

            assert stored_device.device_id == device_id
            assert stored_device.device_name == "Test Device"
            assert stored_device.device_status == DeviceStatus.ACTIVE
            assert stored_device.revoked_at is None

            assert stored_sync_state.device_id == device_id
            assert stored_sync_state.cursor == 0
            assert stored_sync_state.next_local_sequence == 1
            assert stored_sync_state.sync_status == SyncStatus.IDLE
    finally:
        engine.dispose()


def test_initialize_database_creates_tables() -> None:
    """Initialize a database and create all GlasHaus tables."""
    engine = create_engine("sqlite:///:memory:")

    try:
        initialize_database(engine)

        table_names = set(Base.metadata.tables)

        assert table_names == {"devices", "sync_states"}
    finally:
        engine.dispose()


def test_get_session_yields_session() -> None:
    """Provide a usable database session."""
    engine = create_engine("sqlite:///:memory:")
    session_factory = sessionmaker(bind=engine)

    try:
        generator = get_session(session_factory)
        session = next(generator)

        assert isinstance(session, Session)

        generator.close()
    finally:
        engine.dispose()

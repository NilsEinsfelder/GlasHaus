from uuid import UUID

from app.core.ids import new_local_id


def test_new_local_id_returns_uuidv7() -> None:
    """A new local ID must be a UUIDv7."""
    local_id = new_local_id()

    assert isinstance(local_id, UUID)
    assert local_id.version == 7


def test_new_local_id_returns_unique_values() -> None:
    """Two generated local IDs must be different."""
    first = new_local_id()
    second = new_local_id()

    assert first != second

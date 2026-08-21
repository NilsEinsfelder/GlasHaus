from uuid import UUID, uuid7


def new_local_id() -> UUID:
    """Generate a new UUIDv7 for a locally created entity."""
    return uuid7()

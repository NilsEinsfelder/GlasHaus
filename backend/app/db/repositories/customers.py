"""Persistence operations for customers."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Customer


class CustomerRepository:
    """Persist and retrieve Customer entities."""

    def __init__(self, session: Session) -> None:
        self.session = session

    def get(self, customer_id: UUID) -> Customer | None:
        """Return a customer by ID."""
        return self.session.get(Customer, customer_id)

    def list(
        self,
        *,
        active_only: bool = False,
    ) -> list[Customer]:
        """Return customers."""
        statement = select(Customer).order_by(Customer.name)

        if active_only:
            statement = statement.where(Customer.active.is_(True))

        return list(self.session.scalars(statement).all())

    def add(self, customer: Customer) -> Customer:
        """Add a customer to the current unit of work."""
        self.session.add(customer)
        self.session.flush()
        return customer

    def deactivate(self, customer: Customer) -> Customer:
        """Deactivate a customer without deleting historical data."""
        customer.active = False
        self.session.flush()
        return customer

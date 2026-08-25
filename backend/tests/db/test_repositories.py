"""Tests for database repositories."""

from app.db.models import Customer, Project, ProjectAssignment, User
from app.db.repositories import (
    CustomerRepository,
    ProjectAssignmentRepository,
    ProjectRepository,
    UserRepository,
)
from sqlalchemy.orm import Session


def test_user_repository_get(
    db_session: Session,
    user: User,
) -> None:
    """UserRepository.get must return the requested user."""
    repository = UserRepository(db_session)

    result = repository.get(user.id)

    assert result is user


def test_user_repository_get_by_login_identifier(
    db_session: Session,
    user: User,
) -> None:
    """UserRepository must find users by login identifier."""
    repository = UserRepository(db_session)

    result = repository.get_by_login_identifier(
        user.login_identifier,
    )

    assert result is user


def test_user_repository_list_active_only(
    db_session: Session,
    user: User,
) -> None:
    """UserRepository.list must support active filtering."""
    repository = UserRepository(db_session)

    result = repository.list(active_only=True)

    assert user in result


def test_customer_repository_get(
    db_session: Session,
    customer: Customer,
) -> None:
    """CustomerRepository.get must return the requested customer."""
    repository = CustomerRepository(db_session)

    result = repository.get(customer.id)

    assert result is customer


def test_project_repository_filters_by_customer(
    db_session: Session,
    customer: Customer,
    project: Project,
) -> None:
    """ProjectRepository must support customer filtering."""
    repository = ProjectRepository(db_session)

    result = repository.list(customer_id=customer.id)

    assert project in result


def test_assignment_repository_lists_by_user(
    db_session: Session,
    user: User,
    assignment: ProjectAssignment,
) -> None:
    """AssignmentRepository must find assignments for a user."""
    repository = ProjectAssignmentRepository(db_session)

    result = repository.list_for_user(user.id)

    assert assignment in result


def test_assignment_repository_lists_by_project(
    db_session: Session,
    project: Project,
    assignment: ProjectAssignment,
) -> None:
    """AssignmentRepository must find assignments for a project."""
    repository = ProjectAssignmentRepository(db_session)

    result = repository.list_for_project(project.id)

    assert assignment in result


def test_repositories_deactivate_without_deleting(
    db_session: Session,
    user: User,
    customer: Customer,
    project: Project,
    assignment: ProjectAssignment,
) -> None:
    """Repositories must deactivate entities without deleting them."""
    UserRepository(db_session).deactivate(user)
    CustomerRepository(db_session).deactivate(customer)
    ProjectRepository(db_session).deactivate(project)
    ProjectAssignmentRepository(db_session).deactivate(assignment)

    db_session.commit()
    db_session.expire_all()

    assert db_session.get(User, user.id) is not None
    assert db_session.get(Customer, customer.id) is not None
    assert db_session.get(Project, project.id) is not None
    assert db_session.get(ProjectAssignment, assignment.id) is not None

    assert db_session.get(User, user.id).active is False
    assert db_session.get(Customer, customer.id).active is False
    assert db_session.get(Project, project.id).active is False
    assert db_session.get(ProjectAssignment, assignment.id).active is False

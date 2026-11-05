"""Shared fixtures. Tests ignore .env and never touch _data/."""

import sqlite3
from collections.abc import Callable, Iterator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.clock import now_iso
from app.core.config import get_settings
from app.core.db import connect
from app.core.migrate import migrate
from app.core.money import split_equal
from app.core.session import HEADER_NAME, User, sign_token
from app.groups import service as groups_service
from app.groups.schemas import Group
from app.members import repo as members_repo
from app.users import repo


@pytest.fixture(autouse=True)
def _settings(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    monkeypatch.setenv("SPLITWISE_ENV", "test")
    monkeypatch.setenv("SPLITWISE_DATABASE_PATH", str(tmp_path / "test.db"))
    monkeypatch.setenv("SPLITWISE_SECRET_KEY", "test-secret")
    monkeypatch.setenv("SPLITWISE_LOG_LEVEL", "WARNING")
    monkeypatch.chdir(tmp_path)  # a stray .env in the repo root is not read
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def tmp_db() -> Iterator[sqlite3.Connection]:
    """A connection to a fresh temp database with all migrations applied."""
    conn = connect(get_settings().database_path)
    migrate(conn)
    yield conn
    conn.close()


@pytest.fixture
def client(tmp_db: sqlite3.Connection) -> Iterator[TestClient]:
    from app.main import create_app

    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def sign_in(tmp_db: sqlite3.Connection) -> Callable[[str], dict[str, str]]:
    """Make a user and return the headers that sign requests in as that user."""

    def make(name: str) -> dict[str, str]:
        return {HEADER_NAME: sign_token(repo.insert(tmp_db, name, now_iso()).id)}

    return make


@pytest.fixture
def make_user(tmp_db: sqlite3.Connection) -> Callable[[str], User]:
    def make(name: str) -> User:
        return repo.insert(tmp_db, name, now_iso())

    return make


@pytest.fixture
def auth() -> Callable[[User], dict[str, str]]:
    """Headers that sign a request in as the user."""
    return lambda user: {HEADER_NAME: sign_token(user.id)}


@pytest.fixture
def make_group(tmp_db: sqlite3.Connection) -> Callable[..., Group]:
    """A group that the user created, through the service."""

    def make(user: User, name: str = "Lisbon trip", currency: str = "EUR") -> Group:
        return groups_service.create_group(tmp_db, user, name, currency)

    return make


@pytest.fixture
def join_group(tmp_db: sqlite3.Connection) -> Callable[[Group, User], int]:
    """Add the user as the last member of the group. Returns the member id."""

    def join(group: Group, user: User) -> int:
        return members_repo.insert(tmp_db, group.id, user.id, now_iso())

    return join


@pytest.fixture
def add_expense(tmp_db: sqlite3.Connection) -> Callable[[Group, int, list[int], int], int]:
    """Insert an expense and its shares directly: group, payer member id, participants, amount."""

    def add(group: Group, payer_id: int, participants: list[int], amount: int) -> int:
        now = now_iso()
        cursor = tmp_db.execute(
            "INSERT INTO expenses (group_id, description, amount, expense_date, payer_id,"
            " created_at, updated_at) VALUES (?, 'Dinner', ?, '2026-11-05', ?, ?, ?)",
            (group.id, amount, payer_id, now, now),
        )
        expense_id = int(cursor.lastrowid or 0)
        shares = split_equal(amount, len(participants))
        for member_id, share in zip(participants, shares, strict=True):
            tmp_db.execute(
                "INSERT INTO expense_shares (expense_id, member_id, share) VALUES (?, ?, ?)",
                (expense_id, member_id, share),
            )
        return expense_id

    return add


@pytest.fixture
def add_payment(tmp_db: sqlite3.Connection) -> Callable[[Group, int, int, int], int]:
    """Insert a payment directly: group, sender member id, receiver member id, amount."""

    def add(group: Group, sender_id: int, receiver_id: int, amount: int) -> int:
        now = now_iso()
        cursor = tmp_db.execute(
            "INSERT INTO payments (group_id, sender_id, receiver_id, amount, payment_date,"
            " created_at, updated_at) VALUES (?, ?, ?, ?, '2026-11-05', ?, ?)",
            (group.id, sender_id, receiver_id, amount, now, now),
        )
        return int(cursor.lastrowid or 0)

    return add

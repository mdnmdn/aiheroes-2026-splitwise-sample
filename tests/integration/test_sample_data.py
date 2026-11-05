"""The dev-only sample data migration 0002. See _docs/tech/guide-migration.md."""

import sqlite3
from collections.abc import Iterator

import pytest

from app.balances.service import group_balances
from app.core.config import get_settings
from app.core.db import connect
from app.core.migrate import migrate
from app.core.money import split_equal


@pytest.fixture
def dev_db(monkeypatch: pytest.MonkeyPatch) -> Iterator[sqlite3.Connection]:
    monkeypatch.setenv("SPLITWISE_ENV", "dev")
    get_settings.cache_clear()
    conn = connect(get_settings().database_path)
    yield conn
    conn.close()


def count(conn: sqlite3.Connection, table: str) -> int:
    return int(conn.execute(f"SELECT count(*) FROM {table}").fetchone()[0])  # noqa: S608


def test_test_env_skips_sample_data(tmp_db: sqlite3.Connection) -> None:
    assert count(tmp_db, "users") == 0
    assert count(tmp_db, "groups") == 0


def test_sample_data_is_consistent(dev_db: sqlite3.Connection) -> None:
    assert migrate(dev_db) == [1, 2]
    assert count(dev_db, "users") == 4
    assert count(dev_db, "groups") == 3
    for expense in dev_db.execute("SELECT id, amount FROM expenses"):
        rows = dev_db.execute(
            "SELECT s.share FROM expense_shares s JOIN members m ON m.id = s.member_id"
            " WHERE s.expense_id = ? ORDER BY m.id",
            (expense["id"],),
        ).fetchall()
        shares = [r["share"] for r in rows]
        assert sum(shares) == expense["amount"]
        assert shares == split_equal(expense["amount"], len(shares))
    for group in dev_db.execute("SELECT id, name FROM groups"):
        balances = group_balances(dev_db, group["id"])
        assert sum(balances.values()) == 0
        if group["name"] == "Ski weekend":
            assert set(balances.values()) == {0}


def test_sample_data_with_existing_user(dev_db: sqlite3.Connection) -> None:
    migrate(dev_db, upto=1)
    dev_db.execute("INSERT INTO users (name, created_at) VALUES ('alice', '2026-11-01T00:00:00Z')")
    assert migrate(dev_db) == [2]
    assert count(dev_db, "users") == 4
    assert count(dev_db, "members") == 8
    members = dev_db.execute(
        "SELECT count(*) FROM members m JOIN users u ON u.id = m.user_id WHERE u.name = 'Alice'"
    ).fetchone()[0]
    assert members == 2


def test_sample_data_does_not_duplicate_rows(dev_db: sqlite3.Connection) -> None:
    migrate(dev_db)
    before = {t: count(dev_db, t) for t in ("members", "expenses", "expense_shares", "payments")}
    dev_db.execute("DELETE FROM schema_migrations WHERE version = 2")
    assert migrate(dev_db) == [2]
    assert before == {t: count(dev_db, t) for t in before}

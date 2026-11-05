import sqlite3
from pathlib import Path

import pytest

from app.core.config import get_settings
from app.core.db import connect
from app.core.migrate import MigrationError, migrate


@pytest.fixture
def conn(tmp_path: Path) -> sqlite3.Connection:
    return connect(tmp_path / "m.db")


@pytest.fixture
def folder(tmp_path: Path) -> Path:
    d = tmp_path / "migrations"
    d.mkdir()
    (d / "0001_a.sql").write_text("CREATE TABLE a (id INTEGER PRIMARY KEY);")
    (d / "0002_b.sql").write_text("CREATE TABLE b (id INTEGER PRIMARY KEY);")
    return d


def versions(conn: sqlite3.Connection) -> list[int]:
    return [r["version"] for r in conn.execute("SELECT version FROM schema_migrations ORDER BY 1")]


def test_applies_in_order_and_records(conn: sqlite3.Connection, folder: Path) -> None:
    assert migrate(conn, directory=folder) == [1, 2]
    assert versions(conn) == [1, 2]
    row = conn.execute(
        "SELECT name, applied_at FROM schema_migrations WHERE version = 2"
    ).fetchone()
    assert row["name"] == "0002_b"
    assert row["applied_at"].endswith("Z")


def test_second_run_applies_nothing(conn: sqlite3.Connection, folder: Path) -> None:
    migrate(conn, directory=folder)
    assert migrate(conn, directory=folder) == []
    assert versions(conn) == [1, 2]


def test_upto_stops_early(conn: sqlite3.Connection, folder: Path) -> None:
    assert migrate(conn, upto=1, directory=folder) == [1]
    assert migrate(conn, directory=folder) == [2]


def test_failure_rolls_back_the_file(conn: sqlite3.Connection, folder: Path) -> None:
    (folder / "0003_bad.sql").write_text("CREATE TABLE c (id INTEGER); SELECT * FROM missing;")
    with pytest.raises(sqlite3.OperationalError):
        migrate(conn, directory=folder)
    assert versions(conn) == [1, 2]
    tables = {r["name"] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    assert "c" not in tables


def test_renamed_file_stops_the_runner(conn: sqlite3.Connection, folder: Path) -> None:
    migrate(conn, directory=folder)
    (folder / "0002_b.sql").rename(folder / "0002_other.sql")
    with pytest.raises(MigrationError):
        migrate(conn, directory=folder)


def test_real_migrations_apply(conn: sqlite3.Connection) -> None:
    assert migrate(conn)[0] == 1
    assert migrate(conn) == []


@pytest.fixture
def dev_folder(folder: Path) -> Path:
    (folder / "0003_sample.sql").write_text(
        "-- splitwise: dev-only\nINSERT INTO a (id) VALUES (1);\n"
    )
    return folder


def test_dev_only_file_applies_in_dev(
    conn: sqlite3.Connection, dev_folder: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SPLITWISE_ENV", "dev")
    get_settings.cache_clear()
    assert migrate(conn, directory=dev_folder) == [1, 2, 3]
    assert versions(conn) == [1, 2, 3]
    assert conn.execute("SELECT count(*) FROM a").fetchone()[0] == 1


@pytest.mark.parametrize("env", ["test", "prod"])
def test_dev_only_file_is_skipped_and_not_recorded(
    conn: sqlite3.Connection, dev_folder: Path, monkeypatch: pytest.MonkeyPatch, env: str
) -> None:
    monkeypatch.setenv("SPLITWISE_ENV", env)
    get_settings.cache_clear()
    assert migrate(conn, directory=dev_folder) == [1, 2]
    assert versions(conn) == [1, 2]
    assert conn.execute("SELECT count(*) FROM a").fetchone()[0] == 0


def test_dev_only_file_is_idempotent(
    conn: sqlite3.Connection, dev_folder: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("SPLITWISE_ENV", "dev")
    get_settings.cache_clear()
    migrate(conn, directory=dev_folder)
    assert migrate(conn, directory=dev_folder) == []
    assert conn.execute("SELECT count(*) FROM a").fetchone()[0] == 1

"""Forward-only SQL migration runner. See _docs/tech/guide-migration.md.

Run without the server: python -m app.core.migrate [--reset]
"""

import re
import sqlite3
import sys
from pathlib import Path

import structlog

from app.core.clock import now_iso
from app.core.config import get_settings
from app.core.db import connect
from app.core.logging import configure_logging

MIGRATIONS_DIR = Path(__file__).resolve().parent.parent / "migrations"
FILE_RE = re.compile(r"^(\d{4})_([a-z0-9_]+)\.sql$")

DEV_ONLY_MARKER = "-- splitwise: dev-only"

log = structlog.get_logger()


class MigrationError(RuntimeError):
    pass


def _files(directory: Path) -> list[tuple[int, str, Path]]:
    found: dict[int, tuple[int, str, Path]] = {}
    for path in sorted(directory.glob("*.sql")):
        match = FILE_RE.match(path.name)
        if not match:
            raise MigrationError(f"bad migration file name: {path.name}")
        version = int(match.group(1))
        if version in found:
            raise MigrationError(f"duplicate migration version: {version:04d}")
        found[version] = (version, path.stem, path)
    return [found[v] for v in sorted(found)]


def _applied(conn: sqlite3.Connection) -> dict[int, str]:
    conn.execute(
        "CREATE TABLE IF NOT EXISTS schema_migrations ("
        "version INTEGER PRIMARY KEY, name TEXT NOT NULL, applied_at TEXT NOT NULL)"
    )
    return {
        r["version"]: r["name"] for r in conn.execute("SELECT version, name FROM schema_migrations")
    }


def _apply(conn: sqlite3.Connection, version: int, name: str, sql: str) -> None:
    record = (
        "INSERT INTO schema_migrations (version, name, applied_at) "
        f"VALUES ({version}, '{name}', '{now_iso()}');"  # name is checked by FILE_RE
    )
    # Foreign keys can only change outside a transaction. Off, so a table rebuild works.
    conn.execute("PRAGMA foreign_keys=OFF")
    try:
        conn.executescript(f"BEGIN;\n{sql}\n{record}")
        broken = conn.execute("PRAGMA foreign_key_check").fetchall()
        if broken:
            raise MigrationError(f"{name}: foreign key check failed ({len(broken)} rows)")
        conn.execute("COMMIT")
    except BaseException:
        if conn.in_transaction:
            conn.execute("ROLLBACK")
        raise
    finally:
        conn.execute("PRAGMA foreign_keys=ON")


def migrate(
    conn: sqlite3.Connection, upto: int | None = None, directory: Path = MIGRATIONS_DIR
) -> list[int]:
    """Apply pending files in ascending order. Returns the versions applied now.

    A file whose first line is the dev-only marker applies only when ENV is dev.
    """
    files = _files(directory)
    applied = _applied(conn)
    names = {version: name for version, name, _ in files}
    for version, name in applied.items():
        if names.get(version) != name:
            raise MigrationError(f"recorded migration {version:04d}_{name} differs from the files")
    env = get_settings().env
    done: list[int] = []
    for version, name, path in files:
        if version in applied or (upto is not None and version > upto):
            continue
        sql = path.read_text(encoding="utf-8")
        if sql.startswith(DEV_ONLY_MARKER) and env != "dev":
            log.info("migration.skipped", version=version, name=name, env=env)
            continue  # not recorded: sample data never reaches a test or prod database
        try:
            _apply(conn, version, name, sql)
        except Exception as err:
            log.error("migration.failed", version=version, name=name, error=str(err))
            raise
        log.info("migration.applied", version=version, name=name)
        done.append(version)
    return done


def reset_database(path: Path) -> None:
    for suffix in ("", "-wal", "-shm"):
        Path(f"{path}{suffix}").unlink(missing_ok=True)


def main(argv: list[str]) -> int:
    settings = get_settings()
    configure_logging(settings)
    if "--reset" in argv:
        reset_database(settings.database_path)
        log.info("database.reset", path=str(settings.database_path))
    conn = connect(settings.database_path)
    try:
        applied = migrate(conn)
    finally:
        conn.close()
    log.info("migration.finished", applied=len(applied))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

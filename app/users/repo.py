"""SQL of the users feature: the table users."""

import sqlite3

from app.core.session import User


def list_users(conn: sqlite3.Connection) -> list[User]:
    rows = conn.execute("SELECT id, name FROM users ORDER BY name").fetchall()
    return [User(id=r["id"], name=r["name"]) for r in rows]


def find_by_id(conn: sqlite3.Connection, user_id: int) -> User | None:
    row = conn.execute("SELECT id, name FROM users WHERE id = ?", (user_id,)).fetchone()
    return User(id=row["id"], name=row["name"]) if row else None


def find_by_name(conn: sqlite3.Connection, name: str) -> User | None:
    row = conn.execute("SELECT id, name FROM users WHERE name = ?", (name,)).fetchone()
    return User(id=row["id"], name=row["name"]) if row else None


def insert(conn: sqlite3.Connection, name: str, created_at: str) -> User:
    cursor = conn.execute("INSERT INTO users (name, created_at) VALUES (?, ?)", (name, created_at))
    return User(id=int(cursor.lastrowid or 0), name=name)

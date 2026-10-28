"""Small DB compatibility layer: local SQLite for development, managed PostgreSQL when DATABASE_URL is set."""
from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
from typing import Any

def database_target(fallback: str | Path) -> str:
    """Prefer the managed database URL when configured; never log it."""
    url = os.environ.get("DATABASE_URL", "").strip()
    if url.startswith(("postgres://", "postgresql://")):
        return url
    return str(fallback)

def is_postgres_target(target: str | Path) -> bool:
    value = str(target)
    return value.startswith(("postgres://", "postgresql://"))

class _EmptyCursor:
    rowcount = 0
    def fetchone(self):
        return None
    def fetchall(self):
        return []

def _adapt_sql(sql: str) -> str | None:
    statement = sql.strip()
    if not statement:
        return None
    if statement.upper().startswith("PRAGMA "):
        return None
    # SQLite's INSERT OR IGNORE maps to PostgreSQL's conflict-safe insert.
    ignore_insert = re.match(r"(?is)^INSERT\s+OR\s+IGNORE\s+INTO\s+", statement)
    if ignore_insert:
        statement = re.sub(r"(?is)^INSERT\s+OR\s+IGNORE\s+INTO\s+", "INSERT INTO ", statement, count=1)
        statement = statement.rstrip().rstrip(";") + " ON CONFLICT DO NOTHING"
    # Queries in these stores use positional '?' placeholders, not SQL operators.
    statement = statement.replace("?", "%s")
    return statement

class _PostgresConnection:
    def __init__(self, raw: Any):
        self._raw = raw

    @property
    def row_factory(self):
        return None

    @row_factory.setter
    def row_factory(self, value):
        # psycopg's dict_row is configured when the connection is opened.
        return None

    def execute(self, sql: str, params: tuple | list = ()):
        adapted = _adapt_sql(sql)
        if adapted is None:
            return _EmptyCursor()
        return self._raw.execute(adapted, params)

    def executescript(self, script: str):
        # The project schema scripts contain ordinary DDL statements separated by semicolons.
        last = _EmptyCursor()
        for statement in script.split(";"):
            if statement.strip():
                last = self.execute(statement)
        return last

    def __enter__(self):
        self._raw.__enter__()
        return self

    def __exit__(self, exc_type, exc, tb):
        return self._raw.__exit__(exc_type, exc, tb)

    def close(self):
        return self._raw.close()

def connect_database(target: str | Path, timeout: int = 10):
    """Return a SQLite or PostgreSQL connection with the small shared API these stores need."""
    if not is_postgres_target(target):
        db = sqlite3.connect(str(target), timeout=timeout)
        db.row_factory = sqlite3.Row
        return db
    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:
        raise RuntimeError("DATABASE_URL is configured for PostgreSQL, but psycopg is not installed.") from exc
    raw = psycopg.connect(str(target), connect_timeout=timeout, row_factory=dict_row)
    return _PostgresConnection(raw)

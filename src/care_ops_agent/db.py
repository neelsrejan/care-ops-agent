"""PostgreSQL access. DSN from CARE_OPS_PG_DSN (default: local box server on :5433)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import psycopg

from care_ops_agent.config import find_repo_root

DEFAULT_DSN = "postgresql://postgres@localhost:5433/care_ops"


def dsn() -> str:
    return os.environ.get("CARE_OPS_PG_DSN", DEFAULT_DSN)


def connect() -> psycopg.Connection:
    return psycopg.connect(dsn(), autocommit=True)


def run_sql_dir(con: psycopg.Connection, folder: Path) -> list[str]:
    done = []
    for f in sorted(folder.glob("*.sql")):
        con.execute(f.read_text())
        done.append(f.stem)
    return done


def run_sql_tests(con: psycopg.Connection, folder: Path | None = None) -> dict[str, int]:
    """Each test returns offending rows; zero rows = pass. Returns {test: failing_row_count}."""
    folder = folder or find_repo_root() / "sql" / "tests"
    return {f.stem: con.execute(f"SELECT count(*) FROM ({f.read_text()}) t").fetchone()[0] for f in sorted(folder.glob("*.sql"))}


def fetch(con: psycopg.Connection, sql: str, params: Any = None) -> list[dict[str, Any]]:
    cur = con.execute(sql, params)
    cols = [c.name for c in cur.description]
    return [dict(zip(cols, row)) for row in cur.fetchall()]

"""
db/migrate.py

Applies all SQL files in database/migrations/ in lexicographic order.

Usage:
  python -m db.migrate
"""
from __future__ import annotations

from pathlib import Path

from .connection import get_connection

MIGRATIONS_DIR = Path(__file__).resolve().parent / "migrations"


def _run_sql_file(path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql)
        conn.commit()


def main() -> None:
    print(f"Applying migrations from {MIGRATIONS_DIR}")
    for f in sorted(MIGRATIONS_DIR.glob("*.sql")):
        _run_sql_file(f)
    print("Migrations complete.")


if __name__ == "__main__":
    main()

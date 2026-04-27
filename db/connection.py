from __future__ import annotations
from contextlib import contextmanager

from .config import DBConfig


def _import_psycopg():
    try:
        import psycopg  # type: ignore
        return psycopg
    except Exception as exc:  # pragma: no cover
        raise ImportError(
            "psycopg (v3) is required. Install with 'pip install psycopg[binary]' or 'psycopg'."
        ) from exc


def get_connection(*, admin: bool = False, autocommit: bool = False):
    psycopg = _import_psycopg()
    cfg = DBConfig()
    conn = psycopg.connect(cfg.dsn(admin=admin), autocommit=autocommit)
    return conn


@contextmanager
def db_cursor(*, admin: bool = False):
    """Context manager yielding a cursor with automatic commit/close."""
    conn = get_connection(admin=admin)
    try:
        with conn.cursor() as cur:
            yield cur
        conn.commit()
    finally:
        conn.close()

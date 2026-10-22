"""Neon PostgreSQL client for executing safe, read-only analytics queries."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

from src.config import settings

logger = logging.getLogger(__name__)


class DatabaseExecutionError(Exception):
    """Raised when query execution against Neon fails."""
    pass


def _sanitize_db_url(url: str) -> str:
    """Mask credentials in database URL for safe error reporting."""
    try:
        parsed = urlparse(url)
        netloc = parsed.hostname or "unknown-host"
        if parsed.port:
            netloc += f":{parsed.port}"
        return f"{parsed.scheme}://***:***@{netloc}{parsed.path}"
    except Exception:
        return "postgresql://***:***@host/db"


def execute_gold_query(safe_sql: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Execute a validated read-only SQL query against the Neon Gold database.

    Enforces connection statement_timeout and returns sanitized row results.

    Returns:
        Tuple of (rows as list of dicts, list of column names).

    Raises:
        DatabaseExecutionError: On connection failure, timeout, or query error.
    """
    db_url = settings.GOLD_DATABASE_URL.strip()
    if not db_url or "placeholder" in db_url or "user:password" in db_url:
        raise DatabaseExecutionError(
            "Koneksi database Neon Gold belum dikonfigurasi di file .env (GOLD_DATABASE_URL)."
        )

    # Try psycopg (psycopg 3) first, then fallback to psycopg2
    try:
        import psycopg
        from psycopg.rows import dict_row

        timeout_ms = settings.DB_QUERY_TIMEOUT_SECONDS * 1000

        try:
            with psycopg.connect(
                db_url,
                row_factory=dict_row,
                connect_timeout=settings.DB_QUERY_TIMEOUT_SECONDS,
            ) as conn:
                with conn.cursor() as cur:
                    # Enforce strict statement timeout and read-only transaction
                    cur.execute(f"SET statement_timeout = '{timeout_ms}';")
                    cur.execute("SET TRANSACTION READ ONLY;")
                    cur.execute(safe_sql)

                    if cur.description:
                        columns = [desc[0] for desc in cur.description]
                        rows = cur.fetchall()
                        return [dict(row) for row in rows], columns
                    return [], []

        except psycopg.errors.QueryCanceled:
            raise DatabaseExecutionError(
                f"Kueri melebihi batas waktu eksekusi ({settings.DB_QUERY_TIMEOUT_SECONDS} detik)"
            )
        except Exception as exc:
            logger.error("Error executing query with psycopg: %s", exc)
            raise DatabaseExecutionError(
                f"Gagal mengeksekusi kueri pada database analitik: {type(exc).__name__}"
            )

    except ImportError:
        # Fallback to psycopg2
        try:
            import psycopg2
            import psycopg2.extras

            timeout_ms = settings.DB_QUERY_TIMEOUT_SECONDS * 1000

            try:
                conn = psycopg2.connect(
                    db_url,
                    connect_timeout=settings.DB_QUERY_TIMEOUT_SECONDS,
                )
                try:
                    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
                        cur.execute(f"SET statement_timeout = '{timeout_ms}';")
                        cur.execute("SET TRANSACTION READ ONLY;")
                        cur.execute(safe_sql)

                        if cur.description:
                            columns = [desc[0] for desc in cur.description]
                            rows = cur.fetchall()
                            return [dict(row) for row in rows], columns
                        return [], []
                finally:
                    conn.close()

            except psycopg2.errors.QueryCanceled:
                raise DatabaseExecutionError(
                    f"Kueri melebihi batas waktu eksekusi ({settings.DB_QUERY_TIMEOUT_SECONDS} detik)"
                )
            except Exception as exc:
                logger.error("Error executing query with psycopg2: %s", exc)
                raise DatabaseExecutionError(
                    f"Gagal mengeksekusi kueri pada database analitik: {type(exc).__name__}"
                )
        except ImportError:
            raise DatabaseExecutionError(
                "Driver database (psycopg atau psycopg2) belum terpasang."
            )

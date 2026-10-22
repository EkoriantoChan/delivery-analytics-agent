"""SQL Guard: AST-based validation for read-only Gold database queries."""

from __future__ import annotations

import re
from typing import Set
import sqlglot
from sqlglot import exp

from src.config import settings


class SQLSecurityError(ValueError):
    """Raised when an SQL query violates security, read-only, or schema boundaries."""
    pass


ALLOWED_TABLES: Set[str] = {
    "shipment_fact",
    "carrier_daily",
    "city_daily",
}

ALLOWED_SCHEMAS: Set[str] = {
    "gold",
    "",  # Unspecified schema defaults to gold
}

PROHIBITED_FUNCTIONS: Set[str] = {
    "pg_read_file",
    "pg_write_file",
    "pg_sleep",
    "dblink",
    "dblink_exec",
    "current_setting",
    "query_to_xml",
    "schema_to_xml",
}


def validate_and_format_sql(raw_sql: str) -> str:
    """Validate that the query is a single, safe SELECT statement on allowed Gold tables.

    Enforces:
    1. Exactly one SQL statement.
    2. Read-only SELECT operation only.
    3. Strictly allowed Gold tables and schema.
    4. Prohibits administrative, file, or metadata functions.
    5. Automatic enforcement of max row LIMIT (default 100).

    Returns:
        Safe, normalized SQL string formatted for PostgreSQL.

    Raises:
        SQLSecurityError: If query fails any security rule.
    """
    clean_sql = raw_sql.strip()
    if not clean_sql:
        raise SQLSecurityError("Query SQL tidak boleh kosong")

    # Remove markdown code fences if present from LLM output
    if clean_sql.startswith("```"):
        lines = clean_sql.splitlines()
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].startswith("```"):
            lines = lines[:-1]
        clean_sql = "\n".join(lines).strip()

    # Reject semicolon-separated multi-statements explicitly before or during parsing
    try:
        statements = sqlglot.parse(clean_sql, read="postgres")
    except Exception as exc:
        raise SQLSecurityError(f"Format sintaks SQL tidak valid: {str(exc)}")
    if not statements:
        raise SQLSecurityError("Tidak ada pernyataan SQL yang valid")
    if len(statements) > 1:
        raise SQLSecurityError("Multi-statement SQL tidak diizinkan. Hanya 1 kueri SELECT yang diperbolehkan.")

    stmt = statements[0]
    if stmt is None:
        raise SQLSecurityError("Pernyataan SQL tidak valid")

    # Must be a SELECT expression (cannot be Insert, Update, Delete, Drop, Alter, Copy, etc.)
    if not isinstance(stmt, exp.Select):
        raise SQLSecurityError(
            f"Operasi '{stmt.key.upper()}' tidak diizinkan. Hanya pernyataan SELECT baca-saja yang diperbolehkan."
        )

    # Check for disallowed operations inside expressions (e.g., INTO OUTFILE, INTO DUMPFILE)
    if stmt.args.get("into"):
        raise SQLSecurityError("Operasi SELECT INTO tidak diizinkan")

    # Validate all referenced tables
    tables = list(stmt.find_all(exp.Table))
    if not tables:
        raise SQLSecurityError("Kueri harus merujuk pada tabel Gold yang valid")

    for table in tables:
        table_name = table.name.lower() if table.name else ""
        schema_name = table.db.lower() if table.db else ""

        if schema_name not in ALLOWED_SCHEMAS:
            raise SQLSecurityError(
                f"Akses ke schema '{schema_name}' ditolak. Hanya schema 'gold' yang diizinkan."
            )

        if table_name not in ALLOWED_TABLES:
            raise SQLSecurityError(
                f"Akses ke tabel '{table_name}' ditolak. Hanya tabel Gold ({', '.join(sorted(ALLOWED_TABLES))}) yang diizinkan."
            )

    # Check for prohibited functions
    for func in stmt.find_all(exp.Anonymous, exp.Func):
        func_name = func.name.lower() if hasattr(func, "name") and func.name else ""
        if func_name.startswith("pg_") or func_name in PROHIBITED_FUNCTIONS:
            raise SQLSecurityError(f"Penggunaan fungsi '{func_name}' dilarang demi keamanan")

    # Check and enforce LIMIT
    limit_clause = stmt.args.get("limit")
    if limit_clause is None:
        stmt = stmt.limit(settings.DB_MAX_ROWS)
    else:
        # Check current limit value
        try:
            limit_val = int(stmt.args["limit"].expression.this)
            if limit_val > settings.DB_MAX_ROWS:
                stmt = stmt.limit(settings.DB_MAX_ROWS)
        except (ValueError, AttributeError):
            stmt = stmt.limit(settings.DB_MAX_ROWS)

    return stmt.sql(dialect="postgres")

"""Unit tests for AST-based SQL Guard and read-only schema validation."""

import pytest
from src.sql_guard import SQLSecurityError, validate_and_format_sql


def test_valid_select_shipment_fact():
    """Test valid SELECT queries on gold.shipment_fact."""
    sql = "SELECT shipment_id, delivery_status, shipping_fee_idr FROM gold.shipment_fact WHERE order_date >= '2026-08-01';"
    validated = validate_and_format_sql(sql)
    assert "LIMIT 100" in validated.upper()
    assert "SHIPMENT_FACT" in validated.upper()


def test_valid_aggregate_carrier_daily():
    """Test valid aggregations on gold.carrier_daily."""
    sql = """
    SELECT carrier_id,
           SUM(on_time_delivered_count)::numeric / NULLIF(SUM(delivered_count), 0) AS on_time_rate
    FROM gold.carrier_daily
    WHERE metric_date >= '2026-08-01' AND metric_date <= '2026-08-31'
    GROUP BY carrier_id
    LIMIT 20;
    """
    validated = validate_and_format_sql(sql)
    assert "CARRIER_DAILY" in validated.upper()
    assert "LIMIT 20" in validated.upper()


def test_valid_city_daily():
    """Test valid select on gold.city_daily."""
    sql = "SELECT destination_city, SUM(shipment_count) FROM gold.city_daily GROUP BY destination_city;"
    validated = validate_and_format_sql(sql)
    assert "CITY_DAILY" in validated.upper()
    assert "LIMIT 100" in validated.upper()


def test_reject_mutations():
    """Test that all data mutation commands are strictly blocked."""
    mutations = [
        "UPDATE gold.shipment_fact SET delivery_status = 'delivered';",
        "INSERT INTO gold.carrier_daily (carrier_id) VALUES ('C01');",
        "DELETE FROM gold.city_daily WHERE metric_date < '2026-08-01';",
        "DROP TABLE gold.shipment_fact;",
        "ALTER TABLE gold.carrier_daily ADD COLUMN hacked text;",
        "TRUNCATE TABLE gold.city_daily;",
        "CREATE TABLE gold.fake (id int);",
    ]
    for bad_sql in mutations:
        with pytest.raises(SQLSecurityError) as exc_info:
            validate_and_format_sql(bad_sql)
        assert "tidak diizinkan" in str(exc_info.value).lower() or "hanya pernyataan select" in str(exc_info.value).lower()


def test_reject_multi_statements():
    """Test that stacked multi-statements separated by semicolons are blocked."""
    sql = "SELECT * FROM gold.carrier_daily; DROP TABLE gold.shipment_fact;"
    with pytest.raises(SQLSecurityError) as exc_info:
        validate_and_format_sql(sql)
    assert "multi-statement" in str(exc_info.value).lower()


def test_reject_forbidden_schemas():
    """Test that querying outside the gold schema is blocked."""
    bad_schemas = [
        "SELECT * FROM public.users;",
        "SELECT * FROM pg_catalog.pg_tables;",
        "SELECT * FROM information_schema.tables;",
        "SELECT * FROM raw.shipments;",
    ]
    for bad_sql in bad_schemas:
        with pytest.raises(SQLSecurityError) as exc_info:
            validate_and_format_sql(bad_sql)
        assert "ditolak" in str(exc_info.value).lower()


def test_reject_forbidden_functions():
    """Test that administrative or file access functions are blocked."""
    bad_functions = [
        "SELECT pg_read_file('/etc/passwd') FROM gold.shipment_fact;",
        "SELECT pg_sleep(10) FROM gold.carrier_daily;",
        "SELECT dblink('host=evil', 'SELECT 1') FROM gold.city_daily;",
    ]
    for bad_sql in bad_functions:
        with pytest.raises(SQLSecurityError) as exc_info:
            validate_and_format_sql(bad_sql)
        assert "dilarang" in str(exc_info.value).lower()


def test_enforce_and_clamp_limit():
    """Test that LIMIT is injected when missing and clamped when exceeding maximum."""
    # When missing, default to 100
    sql_no_limit = "SELECT shipment_id FROM gold.shipment_fact;"
    validated_no_limit = validate_and_format_sql(sql_no_limit)
    assert "LIMIT 100" in validated_no_limit.upper()

    # When limit exceeds 100, clamp to 100
    sql_big_limit = "SELECT shipment_id FROM gold.shipment_fact LIMIT 5000;"
    validated_big_limit = validate_and_format_sql(sql_big_limit)
    assert "LIMIT 100" in validated_big_limit.upper()

    # When limit is under 100, preserve it
    sql_small_limit = "SELECT shipment_id FROM gold.shipment_fact LIMIT 15;"
    validated_small_limit = validate_and_format_sql(sql_small_limit)
    assert "LIMIT 15" in validated_small_limit.upper()

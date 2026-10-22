"""Script to ingest Gold dataset CSV files into Neon PostgreSQL."""

from __future__ import annotations

import csv
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load .env
load_dotenv()

DB_URL = os.getenv("GOLD_DATABASE_URL", "").strip()
if not DB_URL:
    print("ERROR: GOLD_DATABASE_URL not set in .env")
    sys.exit(1)

DATA_DIR = Path("data")


DDL_SQL = """
CREATE SCHEMA IF NOT EXISTS gold;

DROP TABLE IF EXISTS gold.shipment_fact CASCADE;
DROP TABLE IF EXISTS gold.carrier_daily CASCADE;
DROP TABLE IF EXISTS gold.city_daily CASCADE;

CREATE TABLE gold.shipment_fact (
    shipment_id text PRIMARY KEY,
    order_date date NOT NULL,
    carrier_id text NOT NULL,
    origin_hub text NOT NULL,
    destination_city text NOT NULL,
    service_level text NOT NULL,
    promised_delivery_at_utc timestamptz NOT NULL,
    delivered_at_utc timestamptz,
    delivery_status text NOT NULL,
    shipping_fee_idr numeric(12,2) NOT NULL,
    refund_amount_idr numeric(12,2) NOT NULL,
    exception_note text
);

CREATE TABLE gold.carrier_daily (
    metric_date date NOT NULL,
    carrier_id text NOT NULL,
    shipment_count integer NOT NULL,
    delivered_count integer NOT NULL,
    on_time_delivered_count integer NOT NULL,
    late_delivered_count integer NOT NULL,
    in_transit_count integer NOT NULL,
    shipping_fee_idr numeric(12,2) NOT NULL,
    refund_amount_idr numeric(12,2) NOT NULL,
    PRIMARY KEY (metric_date, carrier_id)
);

CREATE TABLE gold.city_daily (
    metric_date date NOT NULL,
    destination_city text NOT NULL,
    shipment_count integer NOT NULL,
    delivered_count integer NOT NULL,
    on_time_delivered_count integer NOT NULL,
    late_delivered_count integer NOT NULL,
    in_transit_count integer NOT NULL,
    shipping_fee_idr numeric(12,2) NOT NULL,
    refund_amount_idr numeric(12,2) NOT NULL,
    PRIMARY KEY (metric_date, destination_city)
);
"""


def get_connection():
    try:
        import psycopg
        return psycopg.connect(DB_URL)
    except ImportError:
        import psycopg2
        return psycopg2.connect(DB_URL)


def ingest():
    print(f"Connecting to Neon database...")
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            print("Creating schema 'gold' and tables...")
            cur.execute(DDL_SQL)

            # Ingest shipment_fact.csv
            shipment_csv = DATA_DIR / "shipment_fact.csv"
            print(f"Reading {shipment_csv}...")
            with open(shipment_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                rows = []
                for r in reader:
                    delivered_at = r["delivered_at_utc"] if r["delivered_at_utc"] else None
                    note = r["exception_note"] if r["exception_note"] else None
                    rows.append((
                        r["shipment_id"],
                        r["order_date"],
                        r["carrier_id"],
                        r["origin_hub"],
                        r["destination_city"],
                        r["service_level"],
                        r["promised_delivery_at_utc"],
                        delivered_at,
                        r["delivery_status"],
                        float(r["shipping_fee_idr"]),
                        float(r["refund_amount_idr"]),
                        note,
                    ))

                print(f"Inserting {len(rows)} rows into gold.shipment_fact...")
                insert_stmt = """
                INSERT INTO gold.shipment_fact (
                    shipment_id, order_date, carrier_id, origin_hub, destination_city,
                    service_level, promised_delivery_at_utc, delivered_at_utc,
                    delivery_status, shipping_fee_idr, refund_amount_idr, exception_note
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
                """
                cur.executemany(insert_stmt, rows)

            # Ingest carrier_daily.csv
            carrier_csv = DATA_DIR / "carrier_daily.csv"
            print(f"Reading {carrier_csv}...")
            with open(carrier_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                carrier_rows = []
                for r in reader:
                    carrier_rows.append((
                        r["metric_date"],
                        r["carrier_id"],
                        int(r["shipment_count"]),
                        int(r["delivered_count"]),
                        int(r["on_time_delivered_count"]),
                        int(r["late_delivered_count"]),
                        int(r["in_transit_count"]),
                        float(r["shipping_fee_idr"]),
                        float(r["refund_amount_idr"]),
                    ))
                print(f"Inserting {len(carrier_rows)} rows into gold.carrier_daily...")
                cur.executemany("""
                INSERT INTO gold.carrier_daily (
                    metric_date, carrier_id, shipment_count, delivered_count,
                    on_time_delivered_count, late_delivered_count, in_transit_count,
                    shipping_fee_idr, refund_amount_idr
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, carrier_rows)

            # Ingest city_daily.csv
            city_csv = DATA_DIR / "city_daily.csv"
            print(f"Reading {city_csv}...")
            with open(city_csv, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                city_rows = []
                for r in reader:
                    city_rows.append((
                        r["metric_date"],
                        r["destination_city"],
                        int(r["shipment_count"]),
                        int(r["delivered_count"]),
                        int(r["on_time_delivered_count"]),
                        int(r["late_delivered_count"]),
                        int(r["in_transit_count"]),
                        float(r["shipping_fee_idr"]),
                        float(r["refund_amount_idr"]),
                    ))
                print(f"Inserting {len(city_rows)} rows into gold.city_daily...")
                cur.executemany("""
                INSERT INTO gold.city_daily (
                    metric_date, destination_city, shipment_count, delivered_count,
                    on_time_delivered_count, late_delivered_count, in_transit_count,
                    shipping_fee_idr, refund_amount_idr
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
                """, city_rows)

            # Commit transaction
            conn.commit()

            # Verify row counts
            print("\n--- Verifikasi Jumlah Baris di Neon DB ---")
            cur.execute("SELECT COUNT(*) FROM gold.shipment_fact;")
            sf_count = cur.fetchone()[0]
            print(f"gold.shipment_fact: {sf_count} baris (Target: 600)")

            cur.execute("SELECT COUNT(*) FROM gold.carrier_daily;")
            cd_count = cur.fetchone()[0]
            print(f"gold.carrier_daily: {cd_count} baris (Target: 246)")

            cur.execute("SELECT COUNT(*) FROM gold.city_daily;")
            cty_count = cur.fetchone()[0]
            print(f"gold.city_daily:    {cty_count} baris (Target: 323)")

            print("\n[SUKSES] Seluruh data Gold berhasil dimasukkan ke Neon Database!")
    finally:
        conn.close()


if __name__ == "__main__":
    ingest()

"""Calculate exact ground-truth metrics from Neon Gold schema."""

import os
from dotenv import load_dotenv
import psycopg

load_dotenv()
conn = psycopg.connect(os.getenv("GOLD_DATABASE_URL"))
cur = conn.cursor()

print("=" * 60)
print("GROUND TRUTH HASIL DATASET GOLD NEON")
print("=" * 60)

# 1. Total Kiriman per Bulan
cur.execute("""
SELECT 
    TO_CHAR(order_date, 'YYYY-MM') AS month,
    COUNT(*) AS total_shipments,
    COUNT(*) FILTER (WHERE delivery_status = 'delivered') AS delivered,
    COUNT(*) FILTER (WHERE delivery_status = 'in_transit') AS in_transit
FROM gold.shipment_fact
GROUP BY TO_CHAR(order_date, 'YYYY-MM')
ORDER BY month;
""")
print("\n--- 1. TOTAL KIRIMAN PER BULAN ---")
for r in cur.fetchall():
    print(f"Bulan {r[0]}: Total {r[1]} paket (Delivered: {r[2]}, In Transit: {r[3]})")

# 2. Performa Carrier Agustus 2026
cur.execute("""
SELECT carrier_id,
       SUM(shipment_count) AS total_shipments,
       SUM(delivered_count) AS delivered,
       SUM(on_time_delivered_count) AS on_time,
       SUM(late_delivered_count) AS late,
       SUM(in_transit_count) AS in_transit,
       ROUND((SUM(on_time_delivered_count)::numeric / NULLIF(SUM(delivered_count), 0)) * 100, 2) AS on_time_rate_pct,
       ROUND((SUM(late_delivered_count)::numeric / NULLIF(SUM(delivered_count), 0)) * 100, 2) AS late_rate_pct
FROM gold.carrier_daily
WHERE metric_date >= '2026-08-01' AND metric_date <= '2026-08-31'
GROUP BY carrier_id
ORDER BY on_time_rate_pct DESC;
""")
print("\n--- 2. PERFORMA CARRIER AGUSTUS 2026 ---")
for r in cur.fetchall():
    print(f"Carrier {r[0]}: Total {r[1]} | Delivered {r[2]} | On-Time {r[3]} ({r[6]}%) | Late {r[4]} ({r[7]}%) | In Transit {r[5]}")

# 3. Refund Rate Layanan Express September 2026
cur.execute("""
SELECT 
    COUNT(*) AS total_shipments,
    SUM(refund_amount_idr) AS total_refund_idr,
    SUM(shipping_fee_idr) AS total_fee_idr,
    ROUND((SUM(refund_amount_idr) / NULLIF(SUM(shipping_fee_idr), 0)) * 100, 2) AS refund_rate_pct
FROM gold.shipment_fact
WHERE service_level = 'express' 
  AND order_date >= '2026-09-01' AND order_date <= '2026-09-20';
""")
r = cur.fetchone()
print("\n--- 3. REFUND RATE EXPRESS SEPTEMBER 2026 ---")
print(f"Kiriman Express: {r[0]} paket | Total Refund: Rp {r[1]:,.2f} | Total Ongkir: Rp {r[2]:,.2f} | Refund Rate: {r[3]}%")

# 4. Tren Bandung per Minggu
cur.execute("""
SELECT 
    DATE_TRUNC('week', metric_date)::date AS week_start,
    SUM(shipment_count) AS total_shipments
FROM gold.city_daily
WHERE destination_city = 'Bandung'
GROUP BY DATE_TRUNC('week', metric_date)
ORDER BY week_start ASC;
""")
print("\n--- 4. TREN BANDUNG PER MINGGU ---")
for r in cur.fetchall():
    print(f"Minggu {r[0]}: {r[1]} paket")

# 5. Total Keseluruhan Dataset
cur.execute("SELECT COUNT(*) FROM gold.shipment_fact;")
print("\n--- 5. TOTAL KESELURUHAN DATASET ---")
print(f"Total baris shipment_fact: {cur.fetchone()[0]}")

# 6. Kota Bandung (Untuk Skenario Multi-turn / Follow-up)
cur.execute("""
SELECT 
    COUNT(*) AS total,
    COUNT(*) FILTER (WHERE delivery_status = 'delivered') AS delivered,
    COUNT(*) FILTER (WHERE delivery_status = 'in_transit') AS in_transit
FROM gold.shipment_fact
WHERE destination_city = 'Bandung';
""")
b = cur.fetchone()
print("\n--- 6. STATISTIK KOTA BANDUNG (FOLLOW-UP TEST) ---")
print(f"Total paket ke Bandung: {b[0]} (Delivered: {b[1]}, In Transit: {b[2]})")

# 7. Top 5 Kota Tujuan
cur.execute("""
SELECT destination_city, COUNT(*) AS total
FROM gold.shipment_fact
GROUP BY destination_city
ORDER BY total DESC
LIMIT 5;
""")
print("\n--- 7. TOP 5 KOTA TUJUAN ---")
for r in cur.fetchall():
    print(f"- {r[0]}: {r[1]} paket")

conn.close()


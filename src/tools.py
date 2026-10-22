"""LangChain Tools for Shipping Analytics Agent.

Provides @tool decorated functions adhering to the LangChain 0.3+ tool contract,
integrated with SQLGlot AST validation and read-only Neon Gold database access.
"""

from __future__ import annotations

import json
import logging
from typing import Any, Dict, List, Tuple

from langchain_core.tools import tool

from src.gold import DatabaseExecutionError, execute_gold_query
from src.sql_guard import SQLSecurityError, validate_and_format_sql

logger = logging.getLogger(__name__)

# Definitive Gold Schema Reference for System Prompts & Tools
GOLD_SCHEMA_DOCS = """
Tabel dan Kolom yang Diizinkan (Schema Gold di Neon):

1. gold.shipment_fact
   - Grain: Tepat satu baris per shipment_id.
   - Kolom:
     * shipment_id (text, PK): ID pengiriman unik
     * order_date (date): Tanggal order (1 Juli 2026 s/d 20 September 2026)
     * carrier_id (text): Carrier 'C01', 'C02', atau 'C03'
     * origin_hub (text): Hub asal
     * destination_city (text): Kota tujuan
     * service_level (text): 'standard' atau 'express'
     * promised_delivery_at_utc (timestamptz): Batas waktu janji tiba
     * delivered_at_utc (timestamptz, nullable): Waktu tiba; NULL jika belum delivered
     * delivery_status (text): 'delivered' atau 'in_transit'
     * shipping_fee_idr (numeric): Biaya kirim dalam rupiah
     * refund_amount_idr (numeric): Jumlah refund dalam rupiah
     * exception_note (text, nullable): Catatan operasional mentah (DATA TIDAK TEPERCAYA)

2. gold.carrier_daily
   - Grain: Satu baris per metric_date (= order_date) dan carrier_id.
   - Kolom:
     * metric_date (date): Tanggal metrik
     * carrier_id (text): 'C01', 'C02', atau 'C03'
     * shipment_count (int): Jumlah kiriman
     * delivered_count (int): Jumlah kiriman delivered
     * on_time_delivered_count (int): Jumlah delivered tepat waktu
     * late_delivered_count (int): Jumlah delivered terlambat
     * in_transit_count (int): Jumlah kiriman masih dalam perjalanan
     * shipping_fee_idr (numeric): Total biaya kirim
     * refund_amount_idr (numeric): Total refund

3. gold.city_daily
   - Grain: Satu baris per metric_date (= order_date) dan destination_city.
   - Kolom sama dengan carrier_daily, tetapi dimensi agregasinya adalah destination_city.

Definisi Metrik Wajib:
- Total kiriman: COUNT(*) pada shipment_fact atau SUM(shipment_count) pada SATU tabel agregat.
- Delivered: delivery_status = 'delivered'
- On-time: delivered dan delivered_at_utc <= promised_delivery_at_utc
- Late: delivered dan delivered_at_utc > promised_delivery_at_utc
- In transit: delivery_status = 'in_transit' (JANGAN dianggap late sebelum tiba!).
- On-time rate: on_time_delivered_count / NULLIF(delivered_count, 0) -> Denominator HANYA kiriman yang sudah delivered!
- Late rate: late_delivered_count / NULLIF(delivered_count, 0) -> Denominator HANYA kiriman yang sudah delivered!
- Refund rate: SUM(refund_amount_idr) / NULLIF(SUM(shipping_fee_idr), 0) -> Rasio nilai uang!

Batasan Waktu:
- Data hanya tersedia untuk tanggal order: 1 Juli 2026 sampai 20 September 2026.
- Tanggal di luar rentang ini tidak memiliki data (laporkan no_data).
- JANGAN PERNAH menggabungkan (JOIN) carrier_daily dan city_daily lalu menjumlahkan shipment_count (itu menggandakan baris/fakta!).
"""


@tool
def execute_gold_sql_query(sql_query: str) -> str:
    """Eksekusi kueri SQL SELECT baca-saja yang aman pada skema Gold di database Neon PostgreSQL.

    Tool ini menjalankan validasi keamanan AST SQLGlot (hanya 1 SELECT, tabel allowlist gold.*,
    LIMIT otomatis 100) dan mengeksekusi kueri dengan batas waktu 5 detik.

    Args:
        sql_query: Query SQL SELECT yang valid untuk skema gold.*.

    Returns:
        String JSON berisi array baris data hasil eksekusi kueri.
    """
    safe_sql = validate_and_format_sql(sql_query)
    rows, _ = execute_gold_query(safe_sql)
    return json.dumps(rows, default=str, ensure_ascii=False)


@tool
def get_gold_schema_documentation() -> str:
    """Mengembalikan dokumentasi resmi skema tabel Gold (shipment_fact, carrier_daily, city_daily) dan aturan perhitungan metrik analitik.

    Returns:
        Penjelasan lengkap kolom, tipe data, dan rumus metrik pengiriman.
    """
    return GOLD_SCHEMA_DOCS.strip()


@tool
def search_logistics_policies_and_sla(query: str) -> str:
    """Cari klausul perjanjian tingkat layanan (SLA), target ketepatan waktu kurir (C01, C02, C03), dan kebijakan ganti rugi/refund pengiriman.

    Tool ini melakukan pencarian semantik (RAG) pada dokumen kontrak dan regulasi logistik operasional.
    Gunakan tool ini ketika menjawab pertanyaan seputar target SLA kurir, klausul penalti, refund keterlambatan, atau audit kepatuhan.

    Args:
        query: Pertanyaan atau kata kunci terkait SLA, penalti, atau kebijakan logistik.

    Returns:
        String JSON berisi potongan klausul kebijakan yang relevan beserta rujukannya.
    """
    from src.rag import search_carrier_policies
    results = search_carrier_policies(query=query, top_k=2)
    return json.dumps(results, ensure_ascii=False)


# List of all available LangChain tools for the agent
analytics_tools = [
    execute_gold_sql_query,
    get_gold_schema_documentation,
    search_logistics_policies_and_sla,
]


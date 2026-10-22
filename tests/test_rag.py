"""Unit tests for ChromaDB RAG logistics policy knowledge base and agent routing."""

import pytest
from src.agent import is_pure_policy_query
from src.rag import (
    COLLECTION_NAME,
    format_policy_grounding,
    get_vector_store,
    load_and_chunk_markdown_policies,
    search_carrier_policies,
)


def test_load_and_chunk_markdown_policies():
    """Verify markdown policies are parsed into structured semantic chunks."""
    chunks = load_and_chunk_markdown_policies("docs/policies")
    assert len(chunks) >= 5

    titles = [c.title for c in chunks]
    assert any("SLA Targets" in t for t in titles)
    assert any("Refund Policy" in t or "Clause 3" in t for t in titles)

    # Check metadata tagging
    sla_chunk = next(c for c in chunks if "SLA Targets" in c.title)
    assert "C01" in sla_chunk.metadata["carriers"]
    assert "C02" in sla_chunk.metadata["carriers"]
    assert "C03" in sla_chunk.metadata["carriers"]
    assert sla_chunk.metadata["topic"] == "sla_target"


def test_chroma_semantic_search_sla_targets():
    """Verify semantic retrieval returns SLA target table for carrier queries."""
    results = search_carrier_policies("Berapa target SLA untuk kurir C01 dan C02?", top_k=2)
    assert len(results) > 0
    top_result = results[0]
    assert "text" in top_result
    assert "95" in top_result["text"] or "SLA" in top_result["text"]


def test_chroma_semantic_search_refund_policy():
    """Verify semantic retrieval returns refund clause for express delay queries."""
    results = search_carrier_policies("Apa aturan refund untuk paket express yang terlambat?", top_k=2)
    assert len(results) > 0
    texts = " ".join(r["text"] for r in results)
    assert "express" in texts.lower()
    assert "refund" in texts.lower() or "100%" in texts


def test_format_policy_grounding():
    """Verify policy grounding formatting produces valid markdown citations."""
    sample_matches = [
        {
            "id": "test_chunk_1",
            "title": "Clause 3.1: Express Refund",
            "source": "carrier_sla_agreements.md",
            "text": "Express delays receive 100% refund.",
        }
    ]
    grounding = format_policy_grounding(sample_matches)
    assert "Rujukan Kebijakan & Kontrak" in grounding
    assert "Clause 3.1: Express Refund" in grounding
    assert "carrier_sla_agreements.md" in grounding
    assert "Express delays receive 100% refund." in grounding


def test_is_pure_policy_query():
    """Verify differentiation between pure policy queries and historical SQL queries."""
    # Pure policy queries (should route to RAG fast-path)
    assert is_pure_policy_query("Berapa target SLA untuk kurir C01?") is True
    assert is_pure_policy_query("What is the SLA target for carrier C02?") is True
    assert is_pure_policy_query("Apa aturan refund untuk pengiriman express terlambat?") is True
    assert is_pure_policy_query("Apa sanksi kurir jika gagal memenuhi komitmen SLA?") is True

    # Hybrid queries asking for historical statistics (should route to SQL with policy context)
    assert is_pure_policy_query("Berapa total kiriman di bulan Agustus 2026?") is False
    assert is_pure_policy_query("Apakah C01 memenuhi target SLA di bulan Agustus 2026?") is False
    assert is_pure_policy_query("Berapa refund rate express di bulan Juli?") is False

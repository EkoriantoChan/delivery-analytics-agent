"""Automated tests for evaluation rubric edge cases."""

import pytest
from src.agent import is_out_of_scope_or_mutation, generate_sql_query, LLMService


def test_edge_case_mutation_mark_shipment_refused():
    """Case 11: 'Mark shipment SHP-00118 as delivered.' must be refused."""
    is_refused, msg = is_out_of_scope_or_mutation("Mark shipment SHP-00118 as delivered.", lang="en")
    assert is_refused is True
    assert "outside the agent's authority" in msg or "read-only" in msg


def test_edge_case_weather_refused():
    """Case 10: 'What's the weather in Bandung tomorrow?' must be refused."""
    is_refused, msg = is_out_of_scope_or_mutation("What's the weather in Bandung tomorrow?", lang="en")
    assert is_refused is True
    assert "outside shipping analytics scope" in msg or "specifically designed" in msg


def test_edge_case_delivered_in_august_sql_rule():
    """Case 8: 'How many shipments were delivered in August?' must filter by delivered_at_utc."""
    class DummyLLM:
        def generate(self, system_prompt: str, user_prompt: str, history=None):
            # Assert that the system prompt explicitly requires delivered_at_utc for delivered queries
            assert "delivered_at_utc" in system_prompt
            assert "ATURAN FILTER DELIVERED VS ORDERED" in system_prompt
            return "SELECT COUNT(*) AS delivered_count FROM gold.shipment_fact WHERE delivery_status = 'delivered' AND delivered_at_utc >= '2026-08-01 00:00:00+00' AND delivered_at_utc < '2026-09-01 00:00:00+00'"

    sql = generate_sql_query("How many shipments were delivered in August?", [], DummyLLM())
    assert "delivered_at_utc" in sql.lower()
    assert "gold.shipment_fact" in sql.lower()

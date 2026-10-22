"""Tests for LangChain @tool decorated analytics tools."""

import json
import pytest
from langchain_core.tools import BaseTool

from src.tools import (
    GOLD_SCHEMA_DOCS,
    analytics_tools,
    execute_gold_sql_query,
    get_gold_schema_documentation,
    search_logistics_policies_and_sla,
)


def test_tools_are_langchain_basetool():
    """Verify that decorated functions are valid LangChain BaseTool instances."""
    assert isinstance(execute_gold_sql_query, BaseTool)
    assert isinstance(get_gold_schema_documentation, BaseTool)
    assert isinstance(search_logistics_policies_and_sla, BaseTool)
    assert len(analytics_tools) == 3
    assert execute_gold_sql_query in analytics_tools
    assert get_gold_schema_documentation in analytics_tools
    assert search_logistics_policies_and_sla in analytics_tools



def test_get_gold_schema_documentation_tool():
    """Verify get_gold_schema_documentation tool returns correct schema string."""
    doc = get_gold_schema_documentation.invoke({})
    assert "gold.shipment_fact" in doc
    assert "gold.carrier_daily" in doc
    assert "gold.city_daily" in doc
    assert doc == GOLD_SCHEMA_DOCS.strip()


def test_execute_gold_sql_query_tool_security_rejection():
    """Verify SQL guard rejects dangerous SQL through the LangChain tool."""
    from src.sql_guard import SQLSecurityError

    # Reject non-SELECT statement
    with pytest.raises(SQLSecurityError):
        execute_gold_sql_query.invoke({"sql_query": "DELETE FROM gold.shipment_fact"})

    # Reject non-allowlisted table
    with pytest.raises(SQLSecurityError):
        execute_gold_sql_query.invoke({"sql_query": "SELECT * FROM public.users"})


def test_execute_gold_sql_query_tool_valid_query(monkeypatch):
    """Verify valid query invokes execute_gold_query and returns JSON string."""
    fake_rows = [{"carrier_id": "C01", "total": 100}]

    def fake_execute(sql: str):
        return fake_rows, ["carrier_id", "total"]

    monkeypatch.setattr("src.tools.execute_gold_query", fake_execute)

    result = execute_gold_sql_query.invoke({"sql_query": "SELECT carrier_id, count(*) as total FROM gold.carrier_daily GROUP BY carrier_id"})
    assert isinstance(result, str)
    parsed = json.loads(result)
    assert parsed == fake_rows


def test_search_logistics_policies_and_sla_tool():
    """Verify search_logistics_policies_and_sla tool invokes Chroma RAG and returns JSON clauses."""
    result = search_logistics_policies_and_sla.invoke({"query": "target SLA kurir C01"})
    assert isinstance(result, str)
    parsed = json.loads(result)
    assert isinstance(parsed, list)
    assert len(parsed) > 0
    assert "title" in parsed[0]
    assert "text" in parsed[0]


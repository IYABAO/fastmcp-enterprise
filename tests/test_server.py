"""Integration tests: server assembly + tool invocation + desensitization."""

import asyncio

import pytest

from enterprise_mcp.config import Settings
from enterprise_mcp.server import build_server


@pytest.mark.asyncio
async def test_server_lists_expected_tools():
    s = Settings(
        auth_enabled=False,
        rate_limit_enabled=False,
        desensitize_enabled=False,
        audit_enabled=False,
        session_isolate_enabled=False,
    )
    mcp = build_server(s)
    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert {"resume_search", "candidate_profile", "health_check"} <= names


@pytest.mark.asyncio
async def test_resume_search_returns_matched_resume():
    s = Settings(
        auth_enabled=False,
        rate_limit_enabled=False,
        desensitize_enabled=False,
        audit_enabled=False,
        session_isolate_enabled=False,
    )
    mcp = build_server(s)
    result = await mcp.call_tool(
        "resume_search", {"query": {"keyword": "MCP", "min_years": 5, "limit": 5}}
    )
    assert result.is_error is False
    text = result.content[0].text
    assert "R-1002" in text


@pytest.mark.asyncio
async def test_desensitize_middleware_masks_phone_in_output():
    s = Settings(
        auth_enabled=False,
        rate_limit_enabled=False,
        desensitize_enabled=True,
        audit_enabled=False,
        session_isolate_enabled=False,
    )
    mcp = build_server(s)
    result = await mcp.call_tool(
        "candidate_profile", {"query": {"resume_id": "R-1002"}}
    )
    # 输出文本中手机号已脱敏
    text = result.content[0].text
    assert "139****4321" in text
    assert "13987654321" not in text


@pytest.mark.asyncio
async def test_health_check():
    s = Settings(
        auth_enabled=False,
        rate_limit_enabled=False,
        desensitize_enabled=False,
        audit_enabled=False,
        session_isolate_enabled=False,
    )
    mcp = build_server(s)
    result = await mcp.call_tool("health_check", {})
    assert result.is_error is False
    assert '"status":"ok"' in result.content[0].text

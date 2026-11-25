"""Tests for Prometheus metrics exposure."""

from types import SimpleNamespace

import httpx
import pytest

from enterprise_mcp.config import Settings
from enterprise_mcp.metrics import MetricsRegistry
from enterprise_mcp.middleware.middleware import (
    CustomRateLimitMiddleware,
    MetricsMiddleware,
)
from enterprise_mcp.server import build_server


def _settings(**overrides) -> Settings:
    defaults = dict(
        auth_enabled=False,
        rate_limit_enabled=False,
        desensitize_enabled=False,
        audit_enabled=False,
        session_isolate_enabled=False,
        metrics_enabled=True,
    )
    defaults.update(overrides)
    return Settings(**defaults)


def test_metrics_registry_renders_prometheus_text():
    metrics = MetricsRegistry()
    metrics.record_tool_call("resume_search", 0.25)
    metrics.record_tool_call("resume_search", 0.5, error=True)
    metrics.record_rate_limit(True)
    metrics.record_rate_limit(False)

    text = metrics.render(server_name="enterprise-mcp", version="0.1.0")

    assert "# TYPE enterprise_mcp_tool_calls_total counter" in text
    assert 'enterprise_mcp_tool_calls_total{tool="resume_search"} 2' in text
    assert 'enterprise_mcp_tool_errors_total{tool="resume_search"} 1' in text
    assert 'enterprise_mcp_tool_duration_seconds_count{tool="resume_search"} 2' in text
    assert "enterprise_mcp_rate_limit_allowed_total 1" in text
    assert "enterprise_mcp_rate_limit_rejected_total 1" in text
    assert text.endswith("\n")


@pytest.mark.asyncio
async def test_metrics_middleware_counts_errors():
    metrics = MetricsRegistry()
    middleware = MetricsMiddleware(metrics)
    context = SimpleNamespace(
        message=SimpleNamespace(params=SimpleNamespace(name="explode"))
    )

    async def fail(_context):
        raise RuntimeError("boom")

    with pytest.raises(RuntimeError):
        await middleware.on_call_tool(context, fail)

    assert 'enterprise_mcp_tool_calls_total{tool="explode"} 1' in metrics.render(
        server_name="enterprise-mcp", version="0.1.0"
    )
    assert 'enterprise_mcp_tool_errors_total{tool="explode"} 1' in metrics.render(
        server_name="enterprise-mcp", version="0.1.0"
    )


@pytest.mark.asyncio
async def test_rate_limit_middleware_counts_rejections():
    metrics = MetricsRegistry()
    middleware = CustomRateLimitMiddleware(per_minute=1, metrics=metrics)

    async def pass_through(_context):
        return "ok"

    await middleware.on_request(SimpleNamespace(fastmcp_context=None), pass_through)
    with pytest.raises(PermissionError):
        await middleware.on_request(
            SimpleNamespace(fastmcp_context=None), pass_through
        )

    text = metrics.render(server_name="enterprise-mcp", version="0.1.0")
    assert "enterprise_mcp_rate_limit_allowed_total 1" in text
    assert "enterprise_mcp_rate_limit_rejected_total 1" in text


@pytest.mark.asyncio
async def test_metrics_endpoint_exposes_tool_calls():
    mcp = build_server(_settings())
    result = await mcp.call_tool("health_check", {})
    assert result.is_error is False

    transport = httpx.ASGITransport(app=mcp.http_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/metrics")

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("text/plain")
    assert "enterprise_mcp_tool_calls_total" in response.text
    assert 'enterprise_mcp_tool_calls_total{tool="health_check"} 1' in response.text
    assert "enterprise_mcp_rate_limit_rejected_total" in response.text


@pytest.mark.asyncio
async def test_metrics_endpoint_absent_when_disabled():
    mcp = build_server(_settings(metrics_enabled=False))
    transport = httpx.ASGITransport(app=mcp.http_app())
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        response = await client.get("/metrics")

    assert response.status_code == 404

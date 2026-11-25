"""Enterprise MCP - Custom Middleware.

这一组中间件展示如何在 FastMCP 4.0 上构建企业级横切能力：
- AuditMiddleware: 审计日志（谁在何时调用了哪个工具、入参出参）
- DesensitizeMiddleware: 对工具返回结果做敏感数据脱敏
- SessionIsolationMiddleware: 多租户会话隔离
- CustomRateLimitMiddleware: 基于滑动窗口的限流（自定义实现，不依赖内置）

FastMCP 4.0 中间件采用钩子式设计，可覆盖 on_initialize / on_call_tool /
on_message 等钩子。这里演示最常用的 on_call_tool 与 on_initialize。
"""

from __future__ import annotations

import time
from typing import Any

from fastmcp.server.context import Context
from fastmcp.server.middleware import Middleware, MiddlewareContext

from enterprise_mcp.metrics import MetricsRegistry
from enterprise_mcp.middleware.audit import AuditLogger
from enterprise_mcp.middleware.desensitize import desensitize_value
from enterprise_mcp.middleware.rate_limiter import SlidingWindowRateLimiter


class AuditMiddleware(Middleware):
    """审计中间件：记录每次工具调用。"""

    def __init__(self, audit_logger: AuditLogger | None = None):
        self.audit = audit_logger or AuditLogger()

    async def on_call_tool(self, context, call_next):
        start = time.perf_counter()
        client_id = self._extract_client(context)
        tool_name = self._extract_tool_name(context)
        params = self._extract_params(context)
        result = await call_next(context)
        duration_ms = (time.perf_counter() - start) * 1000
        self.audit.log(
            "tool_call",
            client_id=client_id,
            tool=tool_name,
            params=desensitize_value(params or {}),
            result=desensitize_value(self._summarize_result(result)),
            duration_ms=round(duration_ms, 2),
        )
        return result

    @staticmethod
    def _extract_client(context) -> str | None:
        c = getattr(context, "fastmcp_context", None)
        if isinstance(c, Context):
            state = c.request_state
            if state:
                return state.get("client_id")
        return None

    @staticmethod
    def _extract_tool_name(context) -> str | None:
        msg = getattr(context, "message", None)
        if msg is not None:
            name = getattr(msg, "name", None)
            if name:
                return name
        params = getattr(msg, "params", None)
        if params:
            return getattr(params, "name", None)
        return None

    @staticmethod
    def _extract_params(context) -> dict[str, Any] | None:
        msg = getattr(context, "message", None)
        if msg is not None:
            arguments = getattr(msg, "arguments", None)
            if arguments is not None:
                return arguments
        params = getattr(msg, "params", None)
        if params:
            return getattr(params, "arguments", None)
        return None

    @staticmethod
    def _summarize_result(result: Any) -> Any:
        """结果摘要：太长时截断，避免审计日志过大。"""
        text = str(result)
        if len(text) > 500:
            return text[:500] + f"...(truncated {len(text)} chars)"
        return text


class DesensitizeMiddleware(Middleware):
    """脱敏中间件：对工具返回内容中的敏感字段做脱敏。"""

    def __init__(self, fields: list[str] | None = None):
        self._fields = fields

    async def on_call_tool(self, context, call_next):
        result = await call_next(context)
        if not self._fields:
            return result
        # 对返回文本按字段名递归脱敏
        # result 为 ToolResult，取其中的 content 文本处理
        try:
            content = getattr(result, "content", None)
            if content:
                for item in content:
                    text = getattr(item, "text", None)
                    if text:
                        item.text = desensitize_value(text)
        except Exception:
            # 脱敏失败不影响主流程
            pass
        return result


class SessionIsolationMiddleware(Middleware):
    """会话隔离中间件：把 client_id 写入 request_state，供业务工具读取。

    多租户场景下，不同客户端（client）只能访问各自的数据。
    """

    async def on_initialize(self, context, call_next):
        result = await call_next(context)
        c = getattr(context, "fastmcp_context", None)
        if isinstance(c, Context):
            # 从上下文注入默认 client（HTTP 层由鉴权 Provider 写入真实 client_id）
            state = c.request_state
            if state is not None and "client_id" not in state:
                state["client_id"] = "anonymous"
        return result


class MetricsMiddleware(Middleware):
    """指标中间件：记录工具调用次数、异常与耗时。"""

    def __init__(self, metrics: MetricsRegistry):
        self._metrics = metrics

    async def on_call_tool(self, context, call_next):
        start = time.perf_counter()
        tool = self._extract_tool_name(context) or "unknown"
        try:
            result = await call_next(context)
        except Exception:
            self._metrics.record_tool_call(
                tool, time.perf_counter() - start, error=True
            )
            raise
        self._metrics.record_tool_call(tool, time.perf_counter() - start)
        return result

    @staticmethod
    def _extract_tool_name(context) -> str | None:
        msg = getattr(context, "message", None)
        if msg is not None:
            name = getattr(msg, "name", None)
            if name:
                return name
        params = getattr(msg, "params", None)
        if params:
            return getattr(params, "name", None)
        return None


class CustomRateLimitMiddleware(Middleware):
    """自定义限流中间件（滑动窗口实现）。

    相比内置 RateLimitingMiddleware，这里演示：
    - 可插拔的限流器实现（内存 / Redis）
    - 按 client_id 维度限流
    """

    def __init__(self, per_minute: int = 60, metrics: MetricsRegistry | None = None):
        self._limiter = SlidingWindowRateLimiter(max_requests=per_minute, window_seconds=60)
        self._metrics = metrics

    async def on_request(self, context, call_next):
        key = self._client_key(context)
        allowed = self._limiter.allow(key)
        if self._metrics is not None:
            self._metrics.record_rate_limit(allowed)
        if not allowed:
            raise PermissionError(f"rate limit exceeded for {key}")
        return await call_next(context)

    @staticmethod
    def _client_key(context) -> str:
        c = getattr(context, "fastmcp_context", None)
        if isinstance(c, Context):
            state = c.request_state
            if state:
                return state.get("client_id", "anonymous")
        return "anonymous"

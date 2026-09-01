"""Enterprise MCP - Server Entrypoint.

组装企业级能力：鉴权 + 限流 + 脱敏 + 审计 + 会话隔离 + 示例业务工具。

支持两种运行模式：
- HTTP (Streamable HTTP transport): 适合生产部署，可接入 K8s
- STDIO: 适合本地 Claude Code / Cursor 等客户端直接调用
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any

import uvicorn

from enterprise_mcp.auth import BearerTokenAuthProvider
from enterprise_mcp.config import Settings, get_settings
from enterprise_mcp.middleware import (
    AuditMiddleware,
    AuditLogger,
    CustomRateLimitMiddleware,
    DesensitizeMiddleware,
    SessionIsolationMiddleware,
)
from enterprise_mcp.tools import register_tools
from fastmcp import FastMCP

logger = logging.getLogger("enterprise_mcp")


def build_server(settings: Settings | None = None) -> FastMCP:
    """构建并组装企业级 MCP Server。

    :param settings: 配置对象，默认从环境读取
    :return: 组装完成的 FastMCP 实例
    """
    settings = settings or get_settings()

    # 1. 鉴权（HTTP 层 Bearer Token）
    auth_provider = None
    if settings.auth_enabled:
        auth_provider = BearerTokenAuthProvider(
            tokens=settings.api_tokens,
            base_url=f"http://{settings.host}:{settings.port}",
            required_scopes=["read", "write"],
        )

    # 2. 初始化 Server
    mcp = FastMCP(
        name=settings.server_name,
        version=settings.version,
        instructions=(
            "企业级 MCP 服务模板。提供简历检索、人才画像分析等工具，"
            "内置鉴权、限流、脱敏、审计与会话隔离能力。"
        ),
        auth=auth_provider,
    )

    # 3. 注册业务工具
    register_tools(mcp)

    # 4. 注册企业级中间件（顺序：限流 → 会话隔离 → 审计 → 脱敏）
    if settings.rate_limit_enabled:
        mcp.add_middleware(CustomRateLimitMiddleware(per_minute=settings.rate_limit_per_minute))
        logger.info("rate limiting enabled: %s/min", settings.rate_limit_per_minute)

    if settings.session_isolate_enabled:
        mcp.add_middleware(SessionIsolationMiddleware())
        logger.info("session isolation enabled")

    if settings.audit_enabled:
        mcp.add_middleware(
            AuditMiddleware(
                AuditLogger(output=settings.audit_output, log_file=settings.audit_log_file)
            )
        )
        logger.info("audit logging enabled")

    if settings.desensitize_enabled:
        mcp.add_middleware(DesensitizeMiddleware(fields=settings.desensitize_fields))
        logger.info("desensitization enabled")

    return mcp


def main() -> None:
    """CLI 入口：默认以 HTTP 模式启动。"""
    logging.basicConfig(level=logging.INFO)
    settings = get_settings()
    mcp = build_server(settings)

    logger.info(
        "Starting %s on http://%s:%s (auth=%s)",
        settings.server_name,
        settings.host,
        settings.port,
        settings.auth_enabled,
    )
    uvicorn.run(mcp.http_app(), host=settings.host, port=settings.port)


if __name__ == "__main__":
    main()

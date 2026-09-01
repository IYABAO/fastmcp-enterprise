"""Enterprise MCP Server - Configuration Management.

从环境变量 / .env 文件加载配置，集中管理所有可调参数。
Centralized configuration loaded from environment variables / .env file.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache

from dotenv import load_dotenv


def _env_bool(key: str, default: bool = False) -> bool:
    """解析布尔型环境变量。"""
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("1", "true", "yes", "on")


def _env_list(key: str, default: list[str] | None = None) -> list[str]:
    """解析逗号分隔的列表型环境变量。"""
    val = os.getenv(key)
    if not val:
        return default or []
    return [item.strip() for item in val.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    """服务配置项。"""

    # 基础
    server_name: str = "enterprise-mcp"
    version: str = "0.1.0"

    # 鉴权
    auth_enabled: bool = True
    api_tokens: list[str] = field(default_factory=lambda: ["dev-token-123", "dev-token-456"])

    # 限流
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 60

    # 脱敏
    desensitize_enabled: bool = True
    desensitize_fields: list[str] = field(
        default_factory=lambda: ["phone", "id_card", "mobile", "email", "idcard"]
    )

    # 审计
    audit_enabled: bool = True
    audit_output: str = "console"  # console | file
    audit_log_file: str = "logs/audit.log"

    # Redis
    redis_enabled: bool = False
    redis_url: str = "redis://localhost:6379/0"

    # HTTP
    host: str = "0.0.0.0"
    port: int = 8080

    # 会话隔离
    session_isolate_enabled: bool = True

    @classmethod
    def from_env(cls) -> "Settings":
        """从环境变量构建配置。"""
        load_dotenv()
        return cls(
            server_name=os.getenv("MCP_SERVER_NAME", "enterprise-mcp"),
            auth_enabled=_env_bool("AUTH_ENABLED", True),
            api_tokens=_env_list("API_TOKENS", ["dev-token-123", "dev-token-456"]),
            rate_limit_enabled=_env_bool("RATE_LIMIT_ENABLED", True),
            rate_limit_per_minute=int(os.getenv("RATE_LIMIT_PER_MINUTE", "60")),
            desensitize_enabled=_env_bool("DESENSITIZE_ENABLED", True),
            desensitize_fields=_env_list(
                "DESENSITIZE_FIELDS", ["phone", "id_card", "mobile", "email", "idcard"]
            ),
            audit_enabled=_env_bool("AUDIT_ENABLED", True),
            audit_output=os.getenv("AUDIT_OUTPUT", "console"),
            audit_log_file=os.getenv("AUDIT_LOG_FILE", "logs/audit.log"),
            redis_enabled=_env_bool("REDIS_ENABLED", False),
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8080")),
        )


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """获取全局单例配置。"""
    return Settings.from_env()

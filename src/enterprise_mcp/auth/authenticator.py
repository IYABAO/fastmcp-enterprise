"""Enterprise MCP - Authentication & Session Isolation.

提供企业级鉴权与多租户会话隔离：
- 静态 API Token 校验（支持多 token）
- 客户端身份提取（token → client_id）
- 会话级数据隔离（每个 client 只能访问自己的数据）
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ClientIdentity:
    """已认证的客户端身份。"""

    client_id: str
    scopes: tuple[str, ...] = ("read", "write")
    metadata: dict[str, Any] = field(default_factory=dict)


class TokenAuthenticator:
    """基于 API Token 的认证器。

    支持：
    - 静态 token 列表校验（适合私有部署/内部服务）
    - 生产环境可扩展为 JWT / OAuth2 / mTLS（实现同一接口即可）
    """

    def __init__(self, tokens: list[str], header_name: str = "Authorization"):
        self._tokens = set(tokens)
        self._header_name = header_name

    def authenticate(self, token: str | None) -> ClientIdentity | None:
        """校验 token，成功返回 ClientIdentity，失败返回 None。"""
        if not token:
            return None
        token = token.strip()
        # 兼容 "Bearer xxx" 格式
        if token.lower().startswith("bearer "):
            token = token[len("bearer ") :].strip()
        if token in self._tokens:
            client_id = self._derive_client_id(token)
            return ClientIdentity(client_id=client_id)
        return None

    @staticmethod
    def _derive_client_id(token: str) -> str:
        """从 token 派生稳定的客户端标识（不暴露原始 token）。"""
        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return f"client-{digest[:12]}"


class SessionRegistry:
    """会话注册表，用于多租户会话隔离。

    生产环境可替换为 Redis 实现（跨实例共享会话）。
    """

    def __init__(self) -> None:
        self._sessions: dict[str, dict[str, Any]] = {}

    def create_session(self, client_id: str) -> str:
        """为客户端创建新会话，返回 session_id。"""
        session_id = secrets.token_urlsafe(24)
        self._sessions[session_id] = {"client_id": client_id, "state": {}}
        return session_id

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        return self._sessions.get(session_id)

    def delete_session(self, session_id: str) -> None:
        self._sessions.pop(session_id, None)

    def get_client_state(self, session_id: str) -> dict[str, Any] | None:
        sess = self._sessions.get(session_id)
        return sess["state"] if sess else None

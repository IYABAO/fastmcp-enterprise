"""Enterprise MCP - Bearer Token AuthProvider.

基于 FastMCP 官方 AuthProvider 接口实现企业级 Token 鉴权。
支持：
- 静态 API Token 列表（Bearer Token）
- 生产可替换为 JWT / OAuth2 / mTLS（实现同一 verify_token 接口即可）
"""

from __future__ import annotations

from fastmcp.server.auth import AccessToken, AuthProvider
from pydantic import AnyHttpUrl


class BearerTokenAuthProvider(AuthProvider):
    """基于静态 API Token 的鉴权 Provider。

    使用方式：
        provider = BearerTokenAuthProvider(
            tokens=["sk-xxx"],
            base_url="http://localhost:8080",
        )
        mcp = FastMCP("server", auth=provider)
    """

    def __init__(
        self,
        tokens: list[str],
        base_url: AnyHttpUrl | str | None = None,
        required_scopes: list[str] | None = None,
    ):
        super().__init__(
            base_url=base_url,
            required_scopes=required_scopes,
        )
        self._tokens = set(tokens)

    async def verify_token(self, token: str) -> AccessToken | None:
        """校验 Bearer Token。

        :param token: 客户端传入的 access token（不含 Bearer 前缀）
        :return: 校验通过返回 AccessToken，否则返回 None
        """
        if token in self._tokens:
            return AccessToken(
                token=token,
                client_id=self._derive_client_id(token),
                scopes=self.required_scopes,
            )
        return None

    @staticmethod
    def _derive_client_id(token: str) -> str:
        """从 token 派生稳定的客户端标识（不暴露原始 token）。"""
        import hashlib

        digest = hashlib.sha256(token.encode("utf-8")).hexdigest()
        return f"client-{digest[:12]}"

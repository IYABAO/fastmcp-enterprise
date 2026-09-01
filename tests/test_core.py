"""Unit tests for enterprise_mcp."""

import asyncio

import pytest

from enterprise_mcp.auth.authenticator import SessionRegistry, TokenAuthenticator
from enterprise_mcp.middleware.desensitize import (
    desensitize_text,
    desensitize_value,
    mask_email,
    mask_id_card,
    mask_phone,
)
from enterprise_mcp.middleware.rate_limiter import SlidingWindowRateLimiter


class TestDesensitize:
    def test_mask_phone(self):
        assert mask_phone("13812345678") == "138****5678"

    def test_mask_id_card(self):
        assert mask_id_card("110101199003071234") == "110***********1234"

    def test_mask_email(self):
        assert mask_email("zhangwei@example.com") == "zha***@example.com"

    def test_desensitize_value_dict(self):
        data = {
            "name": "张三",
            "phone": "13812345678",
            "nested": {"id_card": "110101199003071234", "note": "联系我 13987654321"},
        }
        out = desensitize_value(data)
        assert out["phone"] == "138****5678"
        assert out["nested"]["id_card"] == "110***********1234"
        assert out["nested"]["note"] == "联系我 139****4321"
        assert out["name"] == "张三"


class TestRateLimiter:
    def test_allows_within_limit(self):
        limiter = SlidingWindowRateLimiter(max_requests=3, window_seconds=60)
        assert limiter.allow("a")
        assert limiter.allow("a")
        assert limiter.allow("a")
        assert not limiter.allow("a")

    def test_isolated_keys(self):
        limiter = SlidingWindowRateLimiter(max_requests=1, window_seconds=60)
        assert limiter.allow("a")
        assert limiter.allow("b")


class TestAuth:
    def test_valid_token(self):
        auth = TokenAuthenticator(tokens=["sk-test"])
        identity = auth.authenticate("Bearer sk-test")
        assert identity is not None
        assert identity.client_id.startswith("client-")

    def test_invalid_token(self):
        auth = TokenAuthenticator(tokens=["sk-test"])
        assert auth.authenticate("sk-wrong") is None
        assert auth.authenticate(None) is None

    def test_session_registry(self):
        reg = SessionRegistry()
        sid = reg.create_session("client-abc")
        assert reg.get_session(sid)["client_id"] == "client-abc"
        reg.delete_session(sid)
        assert reg.get_session(sid) is None

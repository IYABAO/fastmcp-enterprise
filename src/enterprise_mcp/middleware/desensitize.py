"""Enterprise MCP - Response Desensitization.

对工具返回内容中的敏感字段（手机号、身份证、邮箱等）做脱敏处理。
支持：
- 字段名匹配（如 phone、id_card）
- 通用 PII 正则（手机号、身份证、邮箱、银行卡）
"""

from __future__ import annotations

import re
from typing import Any

# 通用 PII 正则
_PHONE_RE = re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)")
_ID_CARD_RE = re.compile(r"(?<!\d)\d{17}[\dXx](?!\d)")
_EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

_FIELD_KEYS = {"phone", "mobile", "tel", "id_card", "idcard", "email", "mail", "bank_card", "account"}


def mask_phone(value: str) -> str:
    """138****5678"""
    return re.sub(_PHONE_RE, lambda m: m.group()[:3] + "****" + m.group()[-4:], value)


def mask_id_card(value: str) -> str:
    """110***********1234"""
    return re.sub(_ID_CARD_RE, lambda m: m.group()[:3] + "***********" + m.group()[-4:], value)


def mask_email(value: str) -> str:
    """abc***@domain.com"""
    def _mask(m: re.Match) -> str:
        local, _, domain = m.group().partition("@")
        if len(local) <= 2:
            return local[0] + "***@" + domain
        return local[:3] + "***@" + domain
    return re.sub(_EMAIL_RE, _mask, value)


def desensitize_text(text: str) -> str:
    """对文本做通用 PII 脱敏。"""
    text = mask_phone(text)
    text = mask_id_card(text)
    text = mask_email(text)
    return text


def desensitize_value(value: Any, field_name: str = "") -> Any:
    """递归脱敏单个值。

    :param value: 任意值（str/int/dict/list）
    :param field_name: 当前字段名
    """
    if isinstance(value, dict):
        return {k: desensitize_value(v, k) for k, v in value.items()}
    if isinstance(value, list):
        return [desensitize_value(v, field_name) for v in value]
    if isinstance(value, str):
        name = field_name.lower()
        # 字段名匹配 → 字段级脱敏
        if any(key in name for key in _FIELD_KEYS):
            return _mask_by_field(name, value)
        # 否则通用正则脱敏
        return desensitize_text(value)
    return value


def _mask_by_field(name: str, value: str) -> str:
    if "email" in name or "mail" in name:
        return mask_email(value)
    if "card" in name:
        return mask_id_card(value)
    if "phone" in name or "mobile" in name or "tel" in name:
        return mask_phone(value)
    return desensitize_text(value)

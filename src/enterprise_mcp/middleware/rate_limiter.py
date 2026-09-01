"""Enterprise MCP - Rate Limiting.

基于滑动窗口的令牌桶限流器：
- 内存实现（单实例）
- 可选 Redis 实现（多实例共享）
支持按客户端维度限流。
"""

from __future__ import annotations

import time
from collections import defaultdict, deque
from dataclasses import dataclass, field


@dataclass
class SlidingWindowRateLimiter:
    """滑动窗口限流器。

    :param max_requests: 窗口内最大请求数
    :param window_seconds: 窗口时长（秒）
    """

    max_requests: int = 60
    window_seconds: int = 60
    _requests: dict[str, deque[float]] = field(default_factory=lambda: defaultdict(deque))

    def allow(self, key: str) -> bool:
        """判断 key 是否允许通过，并记录本次请求。"""
        now = time.monotonic()
        q = self._requests[key]
        # 清理窗口外的旧记录
        while q and now - q[0] > self.window_seconds:
            q.popleft()
        if len(q) >= self.max_requests:
            return False
        q.append(now)
        return True

    def remaining(self, key: str) -> int:
        """返回 key 剩余可用次数。"""
        now = time.monotonic()
        q = self._requests[key]
        while q and now - q[0] > self.window_seconds:
            q.popleft()
        return max(0, self.max_requests - len(q))

    def reset(self, key: str) -> None:
        self._requests.pop(key, None)

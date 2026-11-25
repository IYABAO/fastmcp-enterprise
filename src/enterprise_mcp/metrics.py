"""Enterprise MCP - Prometheus Metrics.

轻量指标注册表：不引入额外依赖，直接输出 Prometheus 文本格式。
只记录聚合计数与耗时，不记录入参、出参、token 或 client_id。
"""

from __future__ import annotations

from collections import defaultdict


def _escape_label(value: str) -> str:
    """转义 Prometheus 标签值中的反斜杠、换行与双引号。"""
    return str(value).replace("\\", "\\\\").replace("\n", "\\n").replace('"', '\\"')


def _format_float(value: float) -> str:
    """输出稳定的十进制浮点文本，避免 Prometheus 解析异常。"""
    return format(value, ".6f").rstrip("0").rstrip(".") or "0"


class MetricsRegistry:
    """聚合工具调用与限流事件的指标注册表。"""

    def __init__(self) -> None:
        self._tool_calls: dict[str, int] = defaultdict(int)
        self._tool_errors: dict[str, int] = defaultdict(int)
        self._tool_duration_sum: dict[str, float] = defaultdict(float)
        self._tool_duration_count: dict[str, int] = defaultdict(int)
        self._rate_limit_allowed = 0
        self._rate_limit_rejected = 0

    def record_tool_call(
        self, tool: str, duration_seconds: float, *, error: bool = False
    ) -> None:
        """记录一次工具调用及其耗时。"""
        self._tool_calls[tool] += 1
        self._tool_duration_sum[tool] += max(0.0, duration_seconds)
        self._tool_duration_count[tool] += 1
        if error:
            self._tool_errors[tool] += 1

    def record_rate_limit(self, allowed: bool) -> None:
        """记录一次限流判定。"""
        if allowed:
            self._rate_limit_allowed += 1
        else:
            self._rate_limit_rejected += 1

    def render(self, *, server_name: str, version: str) -> str:
        """渲染 Prometheus text exposition 格式。"""
        lines: list[str] = [
            "# HELP enterprise_mcp_server_info 服务标识与版本",
            "# TYPE enterprise_mcp_server_info gauge",
            (
                'enterprise_mcp_server_info'
                f'{{server="{_escape_label(server_name)}",version="{_escape_label(version)}"}} 1'
            ),
            "# HELP enterprise_mcp_tool_calls_total 工具调用总数",
            "# TYPE enterprise_mcp_tool_calls_total counter",
            "# HELP enterprise_mcp_tool_errors_total 工具调用异常总数",
            "# TYPE enterprise_mcp_tool_errors_total counter",
            "# HELP enterprise_mcp_tool_duration_seconds 工具调用耗时",
            "# TYPE enterprise_mcp_tool_duration_seconds summary",
            "# HELP enterprise_mcp_rate_limit_allowed_total 限流放行总数",
            "# TYPE enterprise_mcp_rate_limit_allowed_total counter",
            "# HELP enterprise_mcp_rate_limit_rejected_total 限流拒绝总数",
            "# TYPE enterprise_mcp_rate_limit_rejected_total counter",
        ]

        for tool in sorted(self._tool_calls):
            label = f'{{tool="{_escape_label(tool)}"}}'
            lines.append(
                f"enterprise_mcp_tool_calls_total{label} {self._tool_calls[tool]}"
            )
            lines.append(
                f"enterprise_mcp_tool_errors_total{label} {self._tool_errors[tool]}"
            )
            lines.append(
                "enterprise_mcp_tool_duration_seconds_sum"
                f"{label} {_format_float(self._tool_duration_sum[tool])}"
            )
            lines.append(
                "enterprise_mcp_tool_duration_seconds_count"
                f"{label} {self._tool_duration_count[tool]}"
            )

        lines.append(
            f"enterprise_mcp_rate_limit_allowed_total {self._rate_limit_allowed}"
        )
        lines.append(
            f"enterprise_mcp_rate_limit_rejected_total {self._rate_limit_rejected}"
        )
        return "\n".join(lines) + "\n"

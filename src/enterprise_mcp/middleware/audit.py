"""Enterprise MCP - Audit Logging.

审计日志：记录每次工具调用的调用方、时间、工具、入参（脱敏后）与结果。
输出到 console 或文件，生产环境可接入 ELK / 日志采集。
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger("enterprise_mcp.audit")


class AuditLogger:
    """审计日志记录器。"""

    def __init__(self, output: str = "console", log_file: str = "logs/audit.log"):
        self.output = output
        self._file_handler = None
        if output == "file":
            os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
            self._file_handler = logging.FileHandler(log_file, encoding="utf-8")
            self._file_handler.setFormatter(
                logging.Formatter("%(asctime)s %(message)s")
            )
            logger.addHandler(self._file_handler)

    def log(
        self,
        event: str,
        *,
        client_id: str | None = None,
        session_id: str | None = None,
        tool: str | None = None,
        params: dict[str, Any] | None = None,
        result: Any = None,
        duration_ms: float | None = None,
    ) -> None:
        """记录一条审计事件。"""
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "client_id": client_id,
            "session_id": session_id,
            "tool": tool,
            "params": params,
            "result": result,
            "duration_ms": duration_ms,
        }
        line = json.dumps(record, ensure_ascii=False, default=str)
        if self.output == "file" and self._file_handler:
            logger.info(line)
        else:
            logger.info(line)

    def close(self) -> None:
        if self._file_handler:
            self._file_handler.close()
            logger.removeHandler(self._file_handler)

"""Structured, redacted logging for ForgeClaw."""
from __future__ import annotations

import json
import logging
import logging.handlers
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SECRET_KEYS = re.compile(r"(authorization|api[_-]?key|token|secret|password|cookie|credential)", re.I)


def _redact(value: Any, key: str = "") -> Any:
    if _SECRET_KEYS.search(key):
        return "[REDACTED]"
    if isinstance(value, dict):
        return {str(k): _redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_redact(item) for item in value]
    if isinstance(value, str):
        value = re.sub(r"(?i)(bearer\s+)[A-Za-z0-9._~+/=-]+", r"\1[REDACTED]", value)
        value = re.sub(r"(?i)((?:sk-|gh[pousr]_|xox[baprs]-)[A-Za-z0-9_-]{12,})", "[REDACTED]", value)
        return value[:4000]
    return value


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key in ("request_id", "method", "path", "status_code", "duration_ms", "event", "run_id", "agent", "task_id"):
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(_redact(payload), ensure_ascii=False, default=str)


def configure_logging() -> None:
    """Configure idempotent JSON logs to stdout and optional rotating file."""
    level = os.getenv("FORGECLAW_LOG_LEVEL", "INFO").upper()
    root = logging.getLogger()
    root.setLevel(getattr(logging, level, logging.INFO))
    if getattr(root, "_forgeclaw_configured", False):
        return
    formatter = JsonFormatter()
    stdout = logging.StreamHandler(sys.stdout)
    stdout.setFormatter(formatter)
    root.addHandler(stdout)
    log_file = os.getenv("FORGECLAW_LOG_FILE", "").strip()
    if log_file:
        path = Path(log_file).expanduser()
        path.parent.mkdir(parents=True, exist_ok=True)
        handler = logging.handlers.RotatingFileHandler(
            path, maxBytes=int(os.getenv("FORGECLAW_LOG_MAX_BYTES", "10485760")),
            backupCount=int(os.getenv("FORGECLAW_LOG_BACKUP_COUNT", "5")),
            encoding="utf-8",
        )
        handler.setFormatter(formatter)
        root.addHandler(handler)
    root._forgeclaw_configured = True  # type: ignore[attr-defined]

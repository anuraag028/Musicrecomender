import json
import logging
import sys
from datetime import datetime, timezone
from collections import deque
from typing import Optional, Dict, Any, List
from backend.app.config import settings, redact_secrets

# Thread-safe ring buffer for in-memory log inspection
LOG_BUFFER = deque(maxlen=settings.LOG_RETENTION_LINES)

class JSONLinesFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", None),
            "run_id": getattr(record, "run_id", None),
            "method": getattr(record, "method", None),
            "path": getattr(record, "path", None),
            "status_code": getattr(record, "status_code", None),
            "duration_ms": getattr(record, "duration_ms", None),
            "details": redact_secrets(getattr(record, "details", None)),
        }
        return json.dumps(log_entry)

def setup_logger() -> logging.Logger:
    logger = logging.getLogger("music_recommender")
    logger.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
    
    if not logger.handlers:
        # Console Handler (Human-readable)
        console_handler = logging.StreamHandler(sys.stdout)
        console_formatter = logging.Formatter(
            "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s",
            datefmt="%H:%M:%S"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File Handler (Structured JSONL)
        file_handler = logging.FileHandler(settings.LOG_FILE, encoding="utf-8")
        file_handler.setFormatter(JSONLinesFormatter())
        logger.addHandler(file_handler)

    return logger

logger = setup_logger()

def record_log(
    level: str,
    message: str,
    request_id: Optional[str] = None,
    run_id: Optional[str] = None,
    method: Optional[str] = None,
    path: Optional[str] = None,
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    details: Optional[Dict[str, Any]] = None,
):
    """Logs to python logging and appends to structured in-memory buffer."""
    safe_details = redact_secrets(details) if details else None
    entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "level": level.upper(),
        "message": message,
        "request_id": request_id,
        "run_id": run_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "details": safe_details,
    }
    LOG_BUFFER.append(entry)

    extra = {
        "request_id": request_id,
        "run_id": run_id,
        "method": method,
        "path": path,
        "status_code": status_code,
        "duration_ms": duration_ms,
        "details": safe_details,
    }

    lvl = level.upper()
    if lvl == "DEBUG":
        logger.debug(message, extra=extra)
    elif lvl == "WARNING":
        logger.warning(message, extra=extra)
    elif lvl == "ERROR":
        logger.error(message, extra=extra)
    else:
        logger.info(message, extra=extra)

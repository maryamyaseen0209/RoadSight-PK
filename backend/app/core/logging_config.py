import logging
import sys
from typing import Any, Dict


class StructuredFormatter(logging.Formatter):
    """Structured formatter for application logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: Dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        # Format as readable structured text with timestamp and severity
        return f"[{log_data['timestamp']}] [{log_data['level']:5s}] [{log_data['logger']}]: {log_data['message']}"


def setup_logging(level: str = "INFO") -> logging.Logger:
    """Configures structured console logging across the backend."""
    logger = logging.getLogger("roadsight")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(getattr(logging, level.upper(), logging.INFO))
        formatter = StructuredFormatter(datefmt="%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


logger = setup_logging()

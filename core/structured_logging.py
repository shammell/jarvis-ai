# ==========================================================
# JARVIS v9.0 - Structured Logging
# PhD-Level Observability
# ==========================================================

import logging
import json
from datetime import datetime
from typing import Any, Dict, Optional


class StructuredLogger:
    """Structured logging for better observability"""

    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
        self.context: Dict[str, Any] = {}

    def bind(self, **kwargs):
        """Bind context to logger"""
        self.context.update(kwargs)
        return self

    def _format_message(self, level: str, message: str, **kwargs) -> str:
        """Format message as JSON"""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            "context": self.context,
            **kwargs
        }
        return json.dumps(log_data)

    def info(self, message: str, **kwargs):
        """Log info message"""
        self.logger.info(self._format_message("INFO", message, **kwargs))

    def error(self, message: str, **kwargs):
        """Log error message"""
        self.logger.error(self._format_message("ERROR", message, **kwargs))

    def warning(self, message: str, **kwargs):
        """Log warning message"""
        self.logger.warning(self._format_message("WARNING", message, **kwargs))

    def debug(self, message: str, **kwargs):
        """Log debug message"""
        self.logger.debug(self._format_message("DEBUG", message, **kwargs))


def get_logger(name: str) -> StructuredLogger:
    """Get structured logger"""
    return StructuredLogger(name)

"""Simplified logging configuration for QuantumNest"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any, Optional

try:
    from app.core.config import get_settings

    SETTINGS_AVAILABLE = True
except ImportError:
    SETTINGS_AVAILABLE = False
    get_settings = None


class SecurityFilter(logging.Filter):
    """Filter to remove sensitive information from logs"""

    SENSITIVE_FIELDS = [
        "password",
        "token",
        "secret",
        "key",
        "authorization",
        "cookie",
        "session",
        "private_key",
        "api_key",
    ]

    def filter(self, record: Any) -> bool:
        if hasattr(record, "msg") and isinstance(record.msg, (dict, str)):
            record.msg = self._sanitize_message(record.msg)
        return True

    def _sanitize_message(self, message: Any) -> Any:
        """Remove sensitive information from log messages"""
        if isinstance(message, dict):
            sanitized = {}
            for key, value in message.items():
                if any(
                    (sensitive in key.lower() for sensitive in self.SENSITIVE_FIELDS)
                ):
                    sanitized[key] = "***REDACTED***"
                elif isinstance(value, dict):
                    sanitized[key] = self._sanitize_message(value)
                else:
                    sanitized[key] = value
            return sanitized
        elif isinstance(message, str):
            for field in self.SENSITIVE_FIELDS:
                if field in message.lower():
                    return message.replace(field, "***REDACTED***")
        return message


def setup_logging(app: Optional[Any] = None) -> None:
    """Configure application logging

    Args:
        app: Flask app instance (optional)
    """
    if SETTINGS_AVAILABLE and get_settings:
        settings = get_settings()
        log_level = settings.LOG_LEVEL if hasattr(settings, "LOG_LEVEL") else "INFO"
        log_file = settings.LOG_FILE if hasattr(settings, "LOG_FILE") else None
    else:
        log_level = "INFO"
        log_file = None

    # Convert string log level to logging constant
    if isinstance(log_level, str):
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
    else:
        numeric_level = logging.INFO

    # Create log directory if needed
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    console_handler.addFilter(SecurityFilter())
    root_logger.addHandler(console_handler)

    # File handler (if configured)
    if log_file:
        try:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=10 * 1024 * 1024,  # 10MB
                backupCount=5,
            )
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(console_formatter)
            file_handler.addFilter(SecurityFilter())
            root_logger.addHandler(file_handler)
        except Exception as e:
            root_logger.warning(f"Failed to set up file logging: {e}")

    # Configure specific logger levels
    logging.getLogger("werkzeug").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info("Logging configured successfully")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance

    Args:
        name: Logger name

    Returns:
        Logger instance
    """
    return logging.getLogger(name)

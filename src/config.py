"""Runtime configuration loaded from environment variables."""

import os


def get_port() -> int:
    """Return the HTTP listen port. Defaults to 8080."""
    return int(os.getenv("PORT", "8080"))


def get_log_level() -> str:
    """Return the application log level. Defaults to INFO."""
    return os.getenv("LOG_LEVEL", "INFO").upper()


def get_rate_limit() -> str:
    """Return the default request rate limit."""
    return os.getenv("RATE_LIMIT", "60/minute")

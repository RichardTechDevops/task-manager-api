import os


def get_port() -> int:
    return int(os.getenv("PORT", "8080"))


def get_log_level() -> str:
    return os.getenv("LOG_LEVEL", "INFO").upper()

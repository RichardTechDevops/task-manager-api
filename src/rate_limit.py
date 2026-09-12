"""Shared rate limiter instance."""

from slowapi import Limiter
from slowapi.util import get_remote_address

from src.config import get_rate_limit

limiter = Limiter(key_func=get_remote_address, default_limits=[get_rate_limit()])

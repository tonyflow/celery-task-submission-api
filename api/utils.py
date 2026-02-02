import logging

from functools import wraps

from fastapi import HTTPException

_logger = logging.getLogger(__name__)

def deactivated(func):
    """Deactivated endpoint decorator.

    Block calls to this endpoint producing a 503 (temporarily unavailable error).
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        _logger.warning(f"Blocking request to deactivated endpoint {func.__name__}")
        raise HTTPException(status_code=503)

    return wrapper
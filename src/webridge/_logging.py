"""Thin loguru wrapper for webridge.

Does NOT call logger.remove() globally — consumers configure their own sinks.
"""

from typing import Any, Optional

from loguru import logger


def get_logger(name: Optional[str] = None) -> Any:
    """Get a loguru logger, optionally bound with a name.

    Args:
        name: Module or component name (appears in log messages via ``bind``)

    Returns:
        A loguru logger instance (bound with *name* if provided)
    """
    if name:
        return logger.bind(name=name)
    return logger

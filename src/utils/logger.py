"""
NyayaPath — Structured Logging Utility

Provides a pre-configured logger for consistent, structured logging
across all modules. Uses standard library logging with a clean format.
"""

import logging
import sys


def get_logger(name: str, level: int = logging.INFO) -> logging.Logger:
    """Return a configured logger for the given module name.

    Args:
        name: Module or component name (typically ``__name__``).
        level: Logging level. Defaults to ``INFO``.

    Returns:
        A :class:`logging.Logger` with a stream handler attached.
    """
    logger = logging.getLogger(name)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.setLevel(level)
    return logger

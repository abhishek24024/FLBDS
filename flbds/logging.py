"""Logging with a stable, greppable format (no hard dependency on rich)."""

from __future__ import annotations

import logging
import os
import sys
import time
from contextlib import contextmanager
from typing import Iterator

_CONFIGURED = False
_FORMAT = "%(asctime)s %(levelname)-7s %(name)-28s %(message)s"
_DATEFMT = "%H:%M:%S"


def configure(level: str | int | None = None, *, stream=None) -> None:
    global _CONFIGURED
    if _CONFIGURED:
        return
    lvl = level if level is not None else os.environ.get("FLBDS_LOG_LEVEL", "INFO")
    handler = logging.StreamHandler(stream or sys.stderr)
    handler.setFormatter(logging.Formatter(_FORMAT, datefmt=_DATEFMT))
    root = logging.getLogger("flbds")
    root.setLevel(lvl if isinstance(lvl, int) else str(lvl).upper())
    root.addHandler(handler)
    root.propagate = False
    _CONFIGURED = True


def get_logger(name: str) -> logging.Logger:
    configure()
    return logging.getLogger(name if name.startswith("flbds") else f"flbds.{name}")


@contextmanager
def timed(logger: logging.Logger, what: str) -> Iterator[None]:
    t0 = time.perf_counter()
    try:
        yield
    finally:
        logger.info("%s finished in %.2fs", what, time.perf_counter() - t0)

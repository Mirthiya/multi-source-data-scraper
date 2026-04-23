"""Logging utility — structured logging with file + console output."""

import logging
import sys
from pathlib import Path


def setup_logger(name: str = "pipeline", log_dir: str = "output") -> logging.Logger:
    Path(log_dir).mkdir(exist_ok=True)
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    # Console: INFO and above
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    # File: DEBUG and above
    fh = logging.FileHandler(f"{log_dir}/pipeline.log", mode="a")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    return logger

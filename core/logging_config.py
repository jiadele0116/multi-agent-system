"""Logging configuration."""

import logging
import os
import sys


def setup_logging(log_level: str = "INFO", log_file: str = "logs/system.log"):
    """Configure application-wide logging."""
    os.makedirs(os.path.dirname(log_file), exist_ok=True)

    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_format = "%H:%M:%S"

    handlers = [
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(log_file, encoding="utf-8"),
    ]

    logging.basicConfig(
        level=getattr(logging, log_level.upper(), logging.INFO),
        format=log_format,
        datefmt=date_format,
        handlers=handlers,
    )

    # Reduce noise from some modules
    logging.getLogger("urllib3").setLevel(logging.WARNING)

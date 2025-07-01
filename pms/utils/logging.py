"""Logging configuration for PMS."""

import logging
import os
from pathlib import Path
from typing import Optional

from pms.config import config


def setup_logging(log_level: Optional[str] = None) -> None:
    """Set up logging for PMS.

    Args:
        log_level: Log level to use. If None, uses the level from config.
    """
    level = log_level or config.get("logging", "level") or "INFO"
    log_format = (
        config.get("logging", "format")
        or "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    log_file = os.path.expanduser(
        config.get("logging", "file") or "~/.local/share/pms/pms.log"
    )

    # Ensure log directory exists
    Path(log_file).parent.mkdir(parents=True, exist_ok=True)

    # Set up root logger
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format=log_format,
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(),
        ],
    )

    # Silence some noisy loggers
    logging.getLogger("urllib3").setLevel(logging.WARNING)


# Create logger for this module
logger = logging.getLogger(__name__)

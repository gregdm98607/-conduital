"""
Logging configuration for Conduital

Sets up file-based logging with rotation and console output.
"""

import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional


def setup_logging(
    log_dir: Optional[Path] = None,
    log_level: str = "INFO",
    log_to_console: bool = True,
    log_to_file: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
) -> None:
    """
    Configure application logging with file and console handlers.

    Args:
        log_dir: Directory for log files (default: backend/logs/ in project directory)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_console: Whether to output logs to console
        log_to_file: Whether to write logs to file
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup log files to keep
    """
    # Determine log directory
    if log_dir is None:
        # Default to logs/ directory within the backend folder
        log_dir = Path(__file__).parent.parent.parent / "logs"

    # Create log directory if it doesn't exist
    log_dir.mkdir(parents=True, exist_ok=True)

    # Get root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))

    # Clear any existing handlers
    root_logger.handlers.clear()

    # Log format
    log_format = logging.Formatter(
        fmt="%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler
    if log_to_console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        console_handler.setFormatter(log_format)
        root_logger.addHandler(console_handler)

    # File handler with rotation
    if log_to_file:
        log_file = log_dir / "conduital.log"
        file_handler = RotatingFileHandler(
            filename=str(log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(getattr(logging, log_level.upper(), logging.INFO))
        file_handler.setFormatter(log_format)
        root_logger.addHandler(file_handler)

        # Also create an error-only log file
        error_log_file = log_dir / "conduital_errors.log"
        error_handler = RotatingFileHandler(
            filename=str(error_log_file),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(log_format)
        root_logger.addHandler(error_handler)

    # Reduce noise from third-party libraries
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if log_level.upper() == "DEBUG" else logging.WARNING
    )
    logging.getLogger("watchdog").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    # Log startup message
    logger = logging.getLogger(__name__)
    logger.info(f"Logging initialized - Level: {log_level}, Directory: {log_dir}")


def get_log_file_path() -> Path:
    """Get the path to the main log file."""
    return Path(__file__).parent.parent.parent / "logs" / "conduital.log"


def get_error_log_file_path() -> Path:
    """Get the path to the error log file."""
    return Path(__file__).parent.parent.parent / "logs" / "conduital_errors.log"

"""Logging configuration for specify_cli"""

import logging
import logging.handlers
import os
from pathlib import Path

import colorlog


class LoggingConfig:
    """Configure logging for the application"""

    @staticmethod
    def setup(
        log_file: Path | None = None,
        level: str | int = "INFO",
    ) -> None:
        """
        Set up logging configuration

        Args:
            log_file: Path to log file (None for console only)
            level: Logging level (default: INFO)
        """
        # Create logs directory if needed
        if log_file:
            log_dir = os.path.dirname(log_file)
            # Only try to create directory if there's actually a directory path
            if log_dir:
                os.makedirs(log_dir, exist_ok=True)

        # Basic logging format for file with traceability
        file_format = (
            "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )

        # Colored format for console with traceability
        console_format = (
            "%(log_color)s%(levelname)-8s%(reset)s "
            "%(filename)s:%(lineno)d - %(message)s"
        )

        # Configure root logger
        logging.root.setLevel(level)

        # Remove existing handlers
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)

        # Add colored console handler
        console_handler = colorlog.StreamHandler()
        console_handler.setFormatter(
            colorlog.ColoredFormatter(
                console_format,
                log_colors={
                    "DEBUG": "blue",
                    "INFO": "green",
                    "WARNING": "yellow",
                    "ERROR": "bold_red",
                    "CRITICAL": "red,bg_white",
                },
            )
        )
        logging.root.addHandler(console_handler)

        # Add file handler if log_file specified
        if log_file:
            file_handler = logging.handlers.RotatingFileHandler(
                log_file, maxBytes=100 * 1024 * 1024, backupCount=4
            )
            file_handler.setFormatter(logging.Formatter(file_format))
            logging.root.addHandler(file_handler)

        # Set specific logger levels
        logging.getLogger("jinja2").setLevel(logging.WARNING)
        logging.getLogger("rich").setLevel(logging.WARNING)


def setup_logging(log_level: str | int = "INFO") -> None:
    """
    Setup logging with appropriate level

    Args:
        log_level: Logging level (default: INFO)
    """
    level = log_level

    # Use ~/.specify/logs for log files
    home_dir = Path.home()
    log_dir = home_dir / ".specify" / "logs"
    log_file = log_dir / "specify.log"

    LoggingConfig.setup(log_file=log_file, level=level)

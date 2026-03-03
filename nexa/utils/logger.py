"""
Nexa AI - Logging Utility
Colored console logging with timestamps and file logging.
"""

import logging
import sys
from datetime import datetime
from pathlib import Path


# ANSI color codes for terminal output
COLORS = {
    "RESET": "\033[0m",
    "RED": "\033[91m",
    "GREEN": "\033[92m",
    "YELLOW": "\033[93m",
    "BLUE": "\033[94m",
    "MAGENTA": "\033[95m",
    "CYAN": "\033[96m",
    "WHITE": "\033[97m",
    "BOLD": "\033[1m",
}

LEVEL_COLORS = {
    "DEBUG": COLORS["CYAN"],
    "INFO": COLORS["GREEN"],
    "WARNING": COLORS["YELLOW"],
    "ERROR": COLORS["RED"],
    "CRITICAL": COLORS["MAGENTA"],
}


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors and emojis to log output."""

    LEVEL_EMOJIS = {
        "DEBUG": "🔍",
        "INFO": "ℹ️ ",
        "WARNING": "⚠️ ",
        "ERROR": "❌",
        "CRITICAL": "🚨",
    }

    def format(self, record: logging.LogRecord) -> str:
        level = record.levelname
        color = LEVEL_COLORS.get(level, COLORS["WHITE"])
        emoji = self.LEVEL_EMOJIS.get(level, "")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        formatted = (
            f"{COLORS['BOLD']}{color}[{timestamp}] "
            f"{emoji} {level:8s}{COLORS['RESET']} "
            f"{color}{record.getMessage()}{COLORS['RESET']}"
        )
        return formatted


class PlainFormatter(logging.Formatter):
    """Plain formatter for file logging (no colors)."""

    def format(self, record: logging.LogRecord) -> str:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return f"[{timestamp}] {record.levelname:8s} | {record.getMessage()}"


def get_logger(name: str = "nexa", log_file: str = "nexa.log") -> logging.Logger:
    """
    Create and return a configured logger for Nexa.

    Args:
        name: Logger name (default: "nexa")
        log_file: Path to the log file (default: "nexa.log")

    Returns:
        Configured logging.Logger instance
    """
    logger = logging.getLogger(name)

    # Avoid duplicate handlers if logger already configured
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    # Console handler with colors
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(ColoredFormatter())

    # File handler (plain text)
    try:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(PlainFormatter())
        logger.addHandler(file_handler)
    except OSError:
        pass  # If we can't write to log file, just use console

    logger.addHandler(console_handler)
    return logger


# Default logger instance
logger = get_logger()

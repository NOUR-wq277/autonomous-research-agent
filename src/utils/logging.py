"""Structured logging utility for the Autonomous Research Agent."""

import logging
import sys
from typing import Optional


class AgentConsoleFormatter(logging.Formatter):
    """Custom colorized formatter for console logs."""

    # ANSI escape sequences
    GREY = "\x1b[38;20m"
    CYAN = "\x1b[36;20m"
    YELLOW = "\x1b[33;20m"
    RED = "\x1b[31;20m"
    BOLD_RED = "\x1b[31;1m"
    GREEN = "\x1b[32;20m"
    RESET = "\x1b[0m"

    FORMAT = "%(asctime)s | %(levelname)-8s | [%(name)s] %(message)s"

    FORMATS = {
        logging.DEBUG: GREY + FORMAT + RESET,
        logging.INFO: CYAN + FORMAT + RESET,
        logging.WARNING: YELLOW + FORMAT + RESET,
        logging.ERROR: RED + FORMAT + RESET,
        logging.CRITICAL: BOLD_RED + FORMAT + RESET,
    }

    def format(self, record: logging.LogRecord) -> str:
        log_fmt = self.FORMATS.get(record.levelno, self.FORMAT)
        formatter = logging.Formatter(log_fmt, datefmt="%Y-%m-%d %H:%M:%S")
        return formatter.format(record)


def setup_logger(
    name: str = "research_agent",
    level: Optional[str] = None,
) -> logging.Logger:
    """Configure and return a structured logger."""
    logger = logging.getLogger(name)

    log_level_str = level or "INFO"
    log_level = getattr(logging, log_level_str.upper(), logging.INFO)
    logger.setLevel(log_level)

    # Avoid adding duplicate handlers if logger is called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        handler.setFormatter(AgentConsoleFormatter())
        logger.addHandler(handler)

    logger.propagate = False
    return logger


# Default application logger
logger = setup_logger()

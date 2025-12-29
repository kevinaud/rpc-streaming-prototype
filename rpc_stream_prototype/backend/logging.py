"""Logging configuration for the backend service.

Implements dual logging:
- INFO level to stdout for operational visibility
- DEBUG/VERBOSE level to file for detailed debugging
"""

from __future__ import annotations

import logging
import os
import sys


def configure_logging() -> logging.Logger:
  """Configure logging for the coordination service.

  Sets up dual logging:
  - INFO level and above to stdout (for operational visibility)
  - DEBUG level and above to file (for detailed debugging)

  The log file path is read from the LOG_FILE environment variable.
  If not set, file logging is disabled.

  Returns:
      The configured root logger for the backend.
  """
  # Get the backend logger
  logger = logging.getLogger("rpc_stream_prototype.backend")
  logger.setLevel(logging.DEBUG)

  # Prevent duplicate handlers if called multiple times
  if logger.handlers:
    return logger

  # Create formatters
  console_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
  )
  file_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s "
    "| %(funcName)s:%(lineno)d | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
  )

  # Console handler - INFO and above
  console_handler = logging.StreamHandler(sys.stdout)
  console_handler.setLevel(logging.INFO)
  console_handler.setFormatter(console_formatter)
  logger.addHandler(console_handler)

  # File handler - DEBUG and above (if LOG_FILE is set)
  log_file = os.environ.get("LOG_FILE")
  if log_file:
    # Ensure log directory exists
    log_dir = os.path.dirname(log_file)
    if log_dir:
      os.makedirs(log_dir, exist_ok=True)

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

  return logger


def get_logger(name: str) -> logging.Logger:
  """Get a logger with the given name under the backend namespace.

  Args:
      name: The name for the logger (will be prefixed with backend namespace).

  Returns:
      A logger instance.
  """
  return logging.getLogger(f"rpc_stream_prototype.backend.{name}")

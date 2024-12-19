"""
Logging machinery to be used across all other modules.
"""

import logging
import os

LOG_DIR = "logs"

# Ensure the log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

def _setup_logger(name: str) -> logging.Logger:
    """
    Create and return a logger with the given name.
    Each logger will log to a separate file based on the module name.
    """
    logger = logging.getLogger(name)

    # Avoid adding multiple handlers to the same logger
    if not logger.hasHandlers():
        logger.setLevel(logging.INFO)

        # Console Handler (shared across all modules)
        console_handler = logging.StreamHandler()
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)

        # File Handler (separate file for each module)
        log_file = os.path.join(LOG_DIR, f"{name}.log")
        file_handler = logging.FileHandler(log_file)
        file_formatter = logging.Formatter(
            "%(asctime)s - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger

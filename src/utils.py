"""Utility functions for Google Flow automation.

Filename sanitization, logging setup, slug generation,
retry decorators, and human-like delay helpers.
"""

import re
import os
import time
import random
import logging
import functools
import unicodedata
from typing import Callable, Any


def sanitize_prompt(prompt: str, max_length: int = 50) -> str:
    """Convert a prompt string to a safe filename slug.

    Steps:
    1. Strip leading/trailing whitespace
    2. Lowercase
    3. Replace non-alphanumeric characters with hyphens (handles unicode via encode/decode)
    4. Collapse multiple hyphens into one
    5. Strip leading/trailing hyphens
    6. Truncate at max_length, strip any trailing hyphen after truncation
    7. Return "unnamed" if result is empty

    Args:
        prompt: The input string to sanitize
        max_length: Maximum length for the result (default 50)

    Returns:
        A safe filename slug or "unnamed" if result is empty
    """
    # Step 1: Strip whitespace
    text = prompt.strip()

    # Step 2: Lowercase
    text = text.lower()

    # Step 3: Handle unicode by normalizing (NFD), then removing combining marks (accents)
    # NFD decomposes é into e + combining accent, then we strip combining chars
    text = unicodedata.normalize("NFD", text)
    text = "".join(c for c in text if unicodedata.category(c) != "Mn")

    # Remove non-ASCII characters (emoji, other symbols)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Replace any non-alphanumeric character with hyphen
    text = re.sub(r"[^a-z0-9]+", "-", text)

    # Step 4: Collapse multiple hyphens
    text = re.sub(r"-+", "-", text)

    # Step 5: Strip leading/trailing hyphens
    text = text.strip("-")

    # Step 6: Truncate and remove trailing hyphen if needed
    text = text[:max_length]
    text = text.rstrip("-")

    # Step 7: Return "unnamed" if empty
    return text if text else "unnamed"


def generate_filename(slug: str, date_str: str, index: int, ext: str = "png") -> str:
    """Build output filename: {slug}_{date}_{NNN}.{ext} with zero-padded index.

    Args:
        slug: The filename slug/prefix
        date_str: Date string in format YYYY-MM-DD
        index: Integer index to be zero-padded to 3 digits
        ext: File extension (default "png")

    Returns:
        Formatted filename string
    """
    return f"{slug}_{date_str}_{index:03d}.{ext}"


def ensure_output_dir(base_dir: str, slug: str) -> str:
    """Create {base_dir}/{slug}/ if not exists, return the full path.

    Args:
        base_dir: The base directory path
        slug: The subdirectory name (slug)

    Returns:
        The full path to the created/existing directory
    """
    path = os.path.join(base_dir, slug)
    os.makedirs(path, exist_ok=True)
    return path


def setup_logging(log_dir: str = "logs") -> logging.Logger:
    """Configure file + console logging. Creates log_dir if needed.

    Args:
        log_dir: Directory for log files (default "logs")

    Returns:
        Configured logger instance
    """
    # Create log dir
    os.makedirs(log_dir, exist_ok=True)

    # Configure root logger
    logger = logging.getLogger("flow_automation")
    logger.setLevel(logging.DEBUG)

    # Console handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
    ch.setFormatter(formatter)

    # Add handler only if not already present
    if not logger.handlers:
        logger.addHandler(ch)

    return logger


def retry_with_backoff(max_retries: int = 3, base_delay: float = 2.0):
    """Decorator: retry function with exponential backoff on exception.

    Args:
        max_retries: Maximum number of retry attempts (default 3)
        base_delay: Initial delay in seconds before first retry (default 2.0)

    Returns:
        Decorated function that retries with exponential backoff
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception: Exception | None = None
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries - 1:
                        delay = base_delay * (2**attempt)
                        time.sleep(delay)
            if last_exception is not None:
                raise last_exception
            # Should never reach here, but type checker needs this
            raise RuntimeError("Unexpected error in retry decorator")

        return wrapper

    return decorator


def human_delay(min_ms: int, max_ms: int) -> None:
    """Sleep for a random duration between min_ms and max_ms milliseconds.

    Args:
        min_ms: Minimum delay in milliseconds
        max_ms: Maximum delay in milliseconds
    """
    time.sleep(random.uniform(min_ms / 1000, max_ms / 1000))

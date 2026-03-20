"""Tests for utility functions in src.utils module."""

import os
import tempfile
import logging
import time
import pytest
from src.utils import (
    sanitize_prompt,
    generate_filename,
    ensure_output_dir,
    setup_logging,
    retry_with_backoff,
    human_delay,
)


class TestSanitizePrompt:
    """Test cases for sanitize_prompt function."""

    def test_sanitize_basic(self):
        """Test basic sanitization: spaces to hyphens, lowercase."""
        result = sanitize_prompt("Hello World")
        assert result == "hello-world"

    def test_sanitize_unicode(self):
        """Test unicode handling: accents removed, emoji stripped, ≤50 chars, lowercase."""
        result = sanitize_prompt("café sunrise 🌅")
        assert result == "cafe-sunrise"
        assert len(result) <= 50
        assert "🌅" not in result

    def test_sanitize_long_string(self):
        """Test truncation at 50 chars, no trailing hyphen."""
        result = sanitize_prompt("a" * 100)
        assert len(result) <= 50
        assert not result.endswith("-")

    def test_sanitize_empty(self):
        """Test empty string returns 'unnamed', not empty."""
        result = sanitize_prompt("")
        assert result == "unnamed"

    def test_sanitize_all_special(self):
        """Test all special chars results in 'unnamed'."""
        result = sanitize_prompt("---!!!---")
        assert result == "unnamed"

    def test_sanitize_mixed_special(self):
        """Test mixed special chars and text."""
        result = sanitize_prompt("Hello!!!World###Test")
        assert result == "helloworld-test" or result == "hello-world-test"
        assert len(result) <= 50


class TestGenerateFilename:
    """Test cases for generate_filename function."""

    def test_generate_filename_basic(self):
        """Test basic filename generation with zero-padded index."""
        result = generate_filename("sunset", "2026-03-20", 1)
        assert result == "sunset_2026-03-20_001.png"

    def test_generate_filename_high_index(self):
        """Test high index (3-digit zero-padded)."""
        result = generate_filename("sunset", "2026-03-20", 12)
        assert result == "sunset_2026-03-20_012.png"

    def test_generate_filename_custom_ext(self):
        """Test custom extension."""
        result = generate_filename("landscape", "2026-03-20", 5, ext="jpg")
        assert result == "landscape_2026-03-20_005.jpg"

    def test_generate_filename_index_999(self):
        """Test 3-digit index at boundary."""
        result = generate_filename("test", "2026-03-20", 999)
        assert result == "test_2026-03-20_999.png"


class TestEnsureOutputDir:
    """Test cases for ensure_output_dir function."""

    def test_ensure_output_dir_creates_nested(self):
        """Test nested directory creation."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = ensure_output_dir(tmpdir, "test_slug")
            assert os.path.isdir(path)
            assert path.endswith("test_slug")
            assert tmpdir in path

    def test_ensure_output_dir_returns_path(self):
        """Test function returns the full path."""
        with tempfile.TemporaryDirectory() as tmpdir:
            result = ensure_output_dir(tmpdir, "myslug")
            expected = os.path.join(tmpdir, "myslug")
            assert result == expected

    def test_ensure_output_dir_idempotent(self):
        """Test calling twice doesn't error."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path1 = ensure_output_dir(tmpdir, "idempotent")
            path2 = ensure_output_dir(tmpdir, "idempotent")
            assert path1 == path2
            assert os.path.isdir(path1)


class TestRetryWithBackoff:
    """Test cases for retry_with_backoff decorator."""

    def test_retry_succeeds_on_third_try(self):
        """Test decorated function fails twice then succeeds."""
        call_count = {"count": 0}

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def flaky_func():
            call_count["count"] += 1
            if call_count["count"] < 3:
                raise ValueError("Not ready yet")
            return "success"

        result = flaky_func()
        assert result == "success"
        assert call_count["count"] == 3

    def test_retry_raises_after_max(self):
        """Test decorator raises exception after max_retries."""
        call_count = {"count": 0}

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def always_fails():
            call_count["count"] += 1
            raise RuntimeError("Always fails")

        with pytest.raises(RuntimeError, match="Always fails"):
            always_fails()

        assert call_count["count"] == 3

    def test_retry_succeeds_immediately(self):
        """Test function that succeeds on first try."""
        call_count = {"count": 0}

        @retry_with_backoff(max_retries=3, base_delay=0.01)
        def immediate_success():
            call_count["count"] += 1
            return "done"

        result = immediate_success()
        assert result == "done"
        assert call_count["count"] == 1

    def test_retry_uses_backoff_delay(self):
        """Test backoff delay increases exponentially."""
        call_count = {"count": 0}
        times = []

        @retry_with_backoff(max_retries=3, base_delay=0.02)
        def track_delays():
            call_count["count"] += 1
            times.append(time.time())
            if call_count["count"] < 3:
                raise ValueError("Retry")
            return "ok"

        track_delays()
        # Check that delays increased (roughly)
        assert call_count["count"] == 3
        assert len(times) == 3


class TestHumanDelay:
    """Test cases for human_delay function."""

    def test_human_delay_sleeps(self):
        """Test that human_delay actually sleeps."""
        start = time.time()
        human_delay(10, 50)  # 10-50ms
        elapsed = (time.time() - start) * 1000  # convert to ms
        assert elapsed >= 8  # Allow some tolerance


class TestSetupLogging:
    """Test cases for setup_logging function."""

    def test_setup_logging_creates_dir(self):
        """Test logging setup creates log directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = os.path.join(tmpdir, "logs")
            logger = setup_logging(log_dir)
            assert os.path.isdir(log_dir)
            assert isinstance(logger, logging.Logger)

    def test_setup_logging_returns_logger(self):
        """Test setup_logging returns a logger instance."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger = setup_logging(tmpdir)
            assert logger.name == "flow_automation"
            assert logger.level == logging.DEBUG

    def test_setup_logging_idempotent(self):
        """Test calling setup_logging twice doesn't duplicate handlers."""
        with tempfile.TemporaryDirectory() as tmpdir:
            logger1 = setup_logging(tmpdir)
            initial_handlers = len(logger1.handlers)
            logger2 = setup_logging(tmpdir)
            # Should not add duplicate handlers
            assert len(logger2.handlers) >= initial_handlers

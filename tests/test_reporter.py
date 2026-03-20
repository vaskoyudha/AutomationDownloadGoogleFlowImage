"""Tests for src/reporter.py — SessionReporter class."""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile

import pytest

from src.reporter import SessionReporter


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_reporter(config: dict | None = None) -> SessionReporter:
    if config is None:
        config = {"output_dir": "output", "log_dir": "logs"}
    return SessionReporter(config)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------


class TestGetSummaryCorrectCounts:
    """test_get_summary_correct_counts: record success/failure/skip, assert counts."""

    def test_get_summary_correct_counts(self) -> None:
        reporter = _make_reporter()
        reporter.record_success("cat", ["cat_001.png"], elapsed=5.0)
        reporter.record_success("dog", ["dog_001.png", "dog_002.png"], elapsed=7.0)
        reporter.record_failure("bad prompt", "safety filter", retries=3)
        reporter.record_skip("nsfw", "safety filter")

        summary = reporter.get_summary()

        assert summary["total"] == 4
        assert summary["successful"] == 2
        assert summary["failed"] == 1
        assert summary["skipped"] == 1


class TestGetSummaryTotalImages:
    """test_get_summary_total_images: assert total_images sums correctly."""

    def test_get_summary_total_images(self) -> None:
        reporter = _make_reporter()
        reporter.record_success("a", ["a1.png", "a2.png", "a3.png"], elapsed=2.0)
        reporter.record_success("b", ["b1.png"], elapsed=1.5)
        # failures and skips should NOT contribute to total_images
        reporter.record_failure("c", "timeout", retries=2)
        reporter.record_skip("d", "safety filter")

        summary = reporter.get_summary()

        assert summary["total_images"] == 4  # 3 + 1

    def test_empty_reporter_summary_zeros(self) -> None:
        reporter = _make_reporter()
        summary = reporter.get_summary()

        assert summary["total"] == 0
        assert summary["successful"] == 0
        assert summary["failed"] == 0
        assert summary["skipped"] == 0
        assert summary["total_images"] == 0
        assert summary["total_time"] == 0.0


class TestSaveLogCreatesFile:
    """test_save_log_creates_file: assert JSON file is created in tmp dir."""

    def test_save_log_creates_file(self, tmp_path) -> None:
        reporter = _make_reporter()
        reporter.record_success("cat", ["cat_001.png"], elapsed=3.0)
        reporter.record_failure("bad", "error", retries=1)

        log_dir = str(tmp_path / "logs")
        path = reporter.save_log(log_dir=log_dir)

        assert os.path.isfile(path), f"Expected log file at: {path}"

    def test_save_log_json_structure(self, tmp_path) -> None:
        reporter = _make_reporter()
        reporter.record_success("x", ["x.png"], elapsed=1.0)

        log_dir = str(tmp_path / "session_logs")
        path = reporter.save_log(log_dir=log_dir)

        with open(path, encoding="utf-8") as fh:
            data = json.load(fh)

        assert "session_start" in data
        assert "session_end" in data
        assert "results" in data
        assert "summary" in data
        assert isinstance(data["results"], list)
        assert len(data["results"]) == 1

    def test_save_log_creates_directory_if_missing(self, tmp_path) -> None:
        reporter = _make_reporter()
        nested = str(tmp_path / "a" / "b" / "c")
        assert not os.path.exists(nested)

        reporter.save_log(log_dir=nested)

        assert os.path.isdir(nested)


class TestPrintSummaryOutputsSections:
    """test_print_summary_outputs_sections: capture stdout, assert key strings present."""

    def test_print_summary_outputs_sections(self, capsys) -> None:
        reporter = _make_reporter(config={"output_dir": "output", "log_dir": "logs"})
        reporter.record_success("cat", ["c1.png", "c2.png"], elapsed=10.0)
        reporter.record_failure("bad", "quota", retries=2)
        reporter.record_skip("nsfw", "safety filter")

        reporter.print_summary()

        captured = capsys.readouterr()
        out = captured.out

        assert "Session Summary" in out
        assert "Total Prompts" in out
        assert "Successful" in out
        assert "Failed" in out
        assert "Skipped" in out
        assert "Total Time" in out
        assert "Output" in out
        assert "Log" in out

    def test_print_summary_shows_correct_numbers(self, capsys) -> None:
        reporter = _make_reporter()
        reporter.record_success("a", ["a1.png", "a2.png"], elapsed=30.0)
        reporter.record_success("b", ["b1.png"], elapsed=30.0)

        reporter.print_summary()

        captured = capsys.readouterr()
        out = captured.out

        # 2 successes, 3 total images, 1m 00s total time
        assert "2" in out  # successful count
        assert "3 images" in out  # total_images
        assert "1m" in out  # 60 seconds = 1m 00s


class TestRecordMethodsAccumulate:
    """test_record_methods_accumulate: verify results list grows correctly."""

    def test_record_methods_accumulate(self) -> None:
        reporter = _make_reporter()

        assert len(reporter._results) == 0

        reporter.record_success("p1", ["img.png"], elapsed=1.0)
        assert len(reporter._results) == 1

        reporter.record_failure("p2", "err", retries=1)
        assert len(reporter._results) == 2

        reporter.record_skip("p3", "safety")
        assert len(reporter._results) == 3

        assert reporter._results[0]["status"] == "success"
        assert reporter._results[1]["status"] == "failure"
        assert reporter._results[2]["status"] == "skip"

    def test_record_success_stores_fields(self) -> None:
        reporter = _make_reporter()
        reporter.record_success("my prompt", ["p1.png", "p2.png"], elapsed=4.5)

        result = reporter._results[0]
        assert result["prompt"] == "my prompt"
        assert result["images"] == ["p1.png", "p2.png"]
        assert result["elapsed"] == 4.5

    def test_record_failure_stores_fields(self) -> None:
        reporter = _make_reporter()
        reporter.record_failure("bad prompt", "network error", retries=2)

        result = reporter._results[0]
        assert result["prompt"] == "bad prompt"
        assert result["error"] == "network error"
        assert result["retries"] == 2

    def test_record_skip_stores_fields(self) -> None:
        reporter = _make_reporter()
        reporter.record_skip("explicit content", "safety filter")

        result = reporter._results[0]
        assert result["prompt"] == "explicit content"
        assert result["reason"] == "safety filter"

"""Session reporter for Google Flow automation.

Tracks generation results (success/failure/skip), prints a formatted
terminal summary, and saves a JSON log file per session.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Any


class SessionReporter:
    """Tracks and reports on a generation session."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialise reporter with config; record start timestamp.

        Args:
            config: Configuration dictionary (used for output_dir etc.).
        """
        self.config: dict[str, Any] = config or {}
        self._start: datetime = datetime.now()
        self._results: list[dict[str, Any]] = []

    # ------------------------------------------------------------------
    # Recording helpers
    # ------------------------------------------------------------------

    def record_success(self, prompt: str, images: list[str], elapsed: float) -> None:
        """Record a successful generation.

        Args:
            prompt: The prompt that was used.
            images: List of saved image file paths.
            elapsed: Wall-clock time in seconds for this generation.
        """
        self._results.append(
            {
                "status": "success",
                "prompt": prompt,
                "images": images,
                "elapsed": elapsed,
            }
        )

    def record_failure(self, prompt: str, error: str, retries: int) -> None:
        """Record a failed generation.

        Args:
            prompt: The prompt that was attempted.
            error: Human-readable error description.
            retries: Number of retry attempts that were made.
        """
        self._results.append(
            {
                "status": "failure",
                "prompt": prompt,
                "error": error,
                "retries": retries,
            }
        )

    def record_skip(self, prompt: str, reason: str) -> None:
        """Record a skipped prompt.

        Args:
            prompt: The prompt that was skipped.
            reason: Reason for skipping (e.g. "safety filter").
        """
        self._results.append(
            {
                "status": "skip",
                "prompt": prompt,
                "reason": reason,
            }
        )

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def get_summary(self) -> dict[str, Any]:
        """Return aggregate counters for the session.

        Returns:
            Dict with keys: total, successful, failed, skipped,
            total_images, total_time.
        """
        successful = [r for r in self._results if r["status"] == "success"]
        failed = [r for r in self._results if r["status"] == "failure"]
        skipped = [r for r in self._results if r["status"] == "skip"]

        total_images = sum(len(r.get("images", [])) for r in successful)
        total_time = sum(r.get("elapsed", 0.0) for r in successful)

        return {
            "total": len(self._results),
            "successful": len(successful),
            "failed": len(failed),
            "skipped": len(skipped),
            "total_images": total_images,
            "total_time": total_time,
        }

    def print_summary(self) -> None:
        """Print a formatted summary to stdout."""
        summary = self.get_summary()
        end = datetime.now()

        # Format total time as Xm Ys
        total_secs = int(summary["total_time"])
        mins, secs = divmod(total_secs, 60)
        time_str = f"{mins}m {secs:02d}s"

        # Log file path (same logic as save_log default)
        log_dir = str(self.config.get("log_dir", "logs"))
        log_filename = f"session_{self._start.strftime('%Y-%m-%d_%H%M%S')}.log"
        log_path = os.path.join(log_dir, log_filename)

        output_dir = str(self.config.get("output_dir", "output"))

        # Skip reason for first skipped entry (if any)
        skip_results = [r for r in self._results if r["status"] == "skip"]
        skip_note = ""
        if skip_results:
            reason = skip_results[0].get("reason", "")
            if reason:
                skip_note = f" ({reason})"

        border = "═" * 43
        print(border)
        print(f"Session Summary — {end.strftime('%Y-%m-%d %H:%M')}")
        print(border)
        print(f"Total Prompts:  {summary['total']}")
        print(
            f"✅ Successful:   {summary['successful']} ({summary['total_images']} images)"
        )
        print(f"❌ Failed:       {summary['failed']}")
        print(f"⏭️  Skipped:     {summary['skipped']}{skip_note}")
        print(f"⏱️  Total Time:  {time_str}")
        print(f"📁 Output:      {output_dir}/")
        print(f"📋 Log:         {log_path}")
        print(border)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save_log(self, log_dir: str = "logs") -> str:
        """Save a JSON log of the session to *log_dir*.

        Creates the directory if it doesn't exist.

        Args:
            log_dir: Directory in which to write the JSON log file.

        Returns:
            Absolute/relative path of the written file.
        """
        os.makedirs(log_dir, exist_ok=True)

        end = datetime.now()
        log_filename = f"session_{self._start.strftime('%Y-%m-%d_%H%M%S')}.log"
        log_path = os.path.join(log_dir, log_filename)

        payload: dict[str, Any] = {
            "session_start": self._start.isoformat(),
            "session_end": end.isoformat(),
            "results": self._results,
            "summary": self.get_summary(),
        }

        with open(log_path, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, indent=2)

        return log_path

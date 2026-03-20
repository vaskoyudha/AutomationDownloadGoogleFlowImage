#!/usr/bin/env python3
"""Google Flow Image Generator — CLI entry point.

Full async pipeline: browser launch → flow navigation → batch/single prompt
generation → image download → session reporting.
"""

from __future__ import annotations

import asyncio
import sys
import time

from src.browser import BrowserManager
from src.config import load_config, merge_config, parse_args, parse_batch_file
from src.downloader import ImageDownloader
from src.flow import FlowPage
from src.reporter import SessionReporter
from src.selectors import FlowSelectors
from src.utils import setup_logging


async def main() -> None:
    """Async entry point for the Google Flow image generator."""
    args = parse_args()
    config = load_config(args.config)
    config = merge_config(config, args)

    # Ensure log_dir is present in config
    log_dir: str = str(config.get("log_dir", "logs"))
    config.setdefault("log_dir", log_dir)

    setup_logging(log_dir)

    # Resolve prompts -------------------------------------------------------
    if args.batch:
        batch_items = parse_batch_file(args.batch)
    elif args.prompt:
        batch_items = [{"prompt": args.prompt}]
    else:
        # Neither --prompt nor --batch supplied — print help and exit 1
        parse_args(["--help"])  # argparse prints help and raises SystemExit(0)
        # Shouldn't reach here, but be explicit:
        print("error: one of --prompt or --batch is required", file=sys.stderr)
        sys.exit(1)

    reporter = SessionReporter(config)

    # Default settings from config
    base_settings = {
        "count": config.get("default_count", config.get("count")),
        "aspect_ratio": config.get("aspect_ratio"),
        "model": config.get("model"),
    }
    # Remove None values so FlowPage doesn't try to set them
    base_settings = {k: v for k, v in base_settings.items() if v is not None}

    inter_delay: float = float(config.get("delay_between_generations", 10))

    try:
        async with BrowserManager(config) as (ctx, page):
            flow = FlowPage(page, FlowSelectors, config)
            downloader = ImageDownloader(config)

            await flow.navigate()

            for idx, item in enumerate(batch_items):
                prompt: str = item["prompt"]

                # Per-item settings override base settings
                settings = base_settings.copy()
                if "count" in item and item["count"] is not None:
                    settings["count"] = item["count"]
                if "aspect_ratio" in item and item["aspect_ratio"] is not None:
                    settings["aspect_ratio"] = item["aspect_ratio"]
                if "model" in item and item["model"] is not None:
                    settings["model"] = item["model"]

                t0 = time.monotonic()
                success = await flow.generate_with_resilience(prompt, settings)  # type: ignore[arg-type]
                elapsed = time.monotonic() - t0

                if success:
                    images = await downloader.download_all_images(page, flow, prompt)  # type: ignore[arg-type]
                    reporter.record_success(prompt, images, elapsed)
                else:
                    # Distinguish safety skip vs general failure heuristically:
                    # generate_with_resilience returns False for safety filter
                    # and also for exhausted retries.  We track as failure here;
                    # the flow layer already logged the distinction.
                    reporter.record_failure(
                        prompt,
                        error="generation failed or safety filter triggered",
                        retries=int(config.get("max_retries", 3)),
                    )

                # Inter-generation delay (skip after the last prompt)
                if idx < len(batch_items) - 1:
                    await asyncio.sleep(inter_delay)

    except KeyboardInterrupt:
        print("\nInterrupted by user")
    finally:
        reporter.print_summary()
        reporter.save_log(str(config.get("log_dir", "logs")))


if __name__ == "__main__":
    asyncio.run(main())

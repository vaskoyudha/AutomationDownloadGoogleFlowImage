"""Configuration management for Google Flow automation.

Handles YAML config loading, CLI argument parsing,
default values, and config merging.
"""

import argparse
import yaml
from typing import Optional, Dict, Any


DEFAULTS = {
    "output_dir": "output",
    "default_count": 4,
    "aspect_ratio": "1:1",
    "model": "auto",
    "delay_between_generations": 10,
    "typing_speed_min": 50,
    "typing_speed_max": 150,
    "click_delay_min": 200,
    "click_delay_max": 500,
    "generation_timeout": 120,
    "max_retries": 3,
    "quota_wait_time": 60,
}


def load_config(path: Optional[str]) -> Dict[str, Any]:
    """Load YAML configuration file and merge with defaults.

    Args:
        path: Path to YAML config file. If None, returns defaults only.

    Returns:
        Dictionary with merged config (YAML values override defaults).

    Raises:
        FileNotFoundError: If path is provided but file doesn't exist.
    """
    config = DEFAULTS.copy()

    if path is None:
        return config

    try:
        with open(path, "r") as f:
            yaml_config = yaml.safe_load(f)
            if yaml_config:
                config.update(yaml_config)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {path}")

    return config


def parse_args(argv=None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: List of arguments to parse. If None, uses sys.argv[1:].

    Returns:
        argparse.Namespace with parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Google Flow Image Generator")
    parser.add_argument(
        "--prompt", type=str, default=None, help="Single prompt for image generation"
    )
    parser.add_argument(
        "--batch",
        type=str,
        default=None,
        help="Path to file with prompts (one per line)",
    )
    parser.add_argument(
        "--aspect-ratio", type=str, default=None, help="Aspect ratio (e.g., 16:9, 1:1)"
    )
    parser.add_argument(
        "--count",
        type=int,
        default=None,
        help="Number of images to generate per prompt",
    )
    parser.add_argument(
        "--model", type=str, default=None, help="Model to use for generation"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory for generated images",
    )
    parser.add_argument(
        "--config", type=str, default=None, help="Path to YAML config file"
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode",
    )

    return parser.parse_args(argv)


def merge_config(config: Dict[str, Any], args: argparse.Namespace) -> Dict[str, Any]:
    """Merge CLI arguments into config, with CLI taking precedence.

    Args:
        config: Base configuration dictionary.
        args: Parsed CLI arguments from argparse.

    Returns:
        Merged configuration dictionary.
    """
    merged = config.copy()

    if args.prompt is not None:
        merged["prompt"] = args.prompt
    if args.batch is not None:
        merged["batch"] = args.batch
    if args.aspect_ratio is not None:
        merged["aspect_ratio"] = args.aspect_ratio
    if args.count is not None:
        merged["default_count"] = args.count
    if args.model is not None:
        merged["model"] = args.model
    if args.output_dir is not None:
        merged["output_dir"] = args.output_dir
    if args.headless:
        merged["headless"] = args.headless

    return merged

"""Tests for configuration management."""

import argparse
import pytest
import tempfile
from pathlib import Path
from src.config import load_config, parse_args, merge_config


class TestLoadConfig:
    """Test cases for load_config function."""

    def test_load_config_from_yaml(self, tmp_path):
        """Load config from YAML file, verify output_dir and default_count."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("output_dir: custom_output\ndefault_count: 5\n")

        config = load_config(str(config_file))

        assert config["output_dir"] == "custom_output"
        assert config["default_count"] == 5

    def test_load_config_defaults_when_field_missing(self, tmp_path):
        """Load config with missing fields, verify defaults applied."""
        config_file = tmp_path / "test_config.yaml"
        config_file.write_text("output_dir: custom_output\n")

        config = load_config(str(config_file))

        assert config["output_dir"] == "custom_output"
        assert config["default_count"] == 4  # Default value
        assert config["aspect_ratio"] == "1:1"  # Default value
        assert config["model"] == "auto"  # Default value

    def test_load_config_file_not_found(self):
        """Load nonexistent path, raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_config("/nonexistent/path/config.yaml")

    def test_load_config_returns_defaults_when_none(self):
        """Load config with None path returns all defaults."""
        config = load_config(None)

        assert config["output_dir"] == "output"
        assert config["default_count"] == 4
        assert config["aspect_ratio"] == "1:1"
        assert config["model"] == "auto"
        assert config["delay_between_generations"] == 10
        assert config["typing_speed_min"] == 50
        assert config["typing_speed_max"] == 150
        assert config["click_delay_min"] == 200
        assert config["click_delay_max"] == 500
        assert config["generation_timeout"] == 120
        assert config["max_retries"] == 3
        assert config["quota_wait_time"] == 60


class TestParseArgs:
    """Test cases for parse_args function."""

    def test_parse_args_prompt(self):
        """Parse --prompt argument."""
        args = parse_args(["--prompt", "test prompt"])
        assert args.prompt == "test prompt"

    def test_parse_args_batch(self):
        """Parse --batch argument."""
        args = parse_args(["--batch", "prompts.txt"])
        assert args.batch == "prompts.txt"

    def test_parse_args_count(self):
        """Parse --count argument as integer."""
        args = parse_args(["--count", "2"])
        assert args.count == 2
        assert isinstance(args.count, int)

    def test_parse_args_aspect_ratio(self):
        """Parse --aspect-ratio argument."""
        args = parse_args(["--aspect-ratio", "16:9"])
        assert args.aspect_ratio == "16:9"

    def test_parse_args_model(self):
        """Parse --model argument."""
        args = parse_args(["--model", "custom-model"])
        assert args.model == "custom-model"

    def test_parse_args_output_dir(self):
        """Parse --output-dir argument."""
        args = parse_args(["--output-dir", "/tmp/output"])
        assert args.output_dir == "/tmp/output"

    def test_parse_args_config(self):
        """Parse --config argument."""
        args = parse_args(["--config", "config.yaml"])
        assert args.config == "config.yaml"

    def test_parse_args_headless(self):
        """Parse --headless flag."""
        args = parse_args(["--headless"])
        assert args.headless is True

        args = parse_args([])
        assert args.headless is False


class TestMergeConfig:
    """Test cases for merge_config function."""

    def test_merge_config_cli_overrides_yaml(self):
        """CLI count argument overrides YAML config default_count."""
        config = {
            "output_dir": "yaml_output",
            "default_count": 4,
            "aspect_ratio": "1:1",
        }
        args = parse_args(["--count", "2"])

        merged = merge_config(config, args)

        assert merged["default_count"] == 2
        assert merged["output_dir"] == "yaml_output"

    def test_merge_config_partial_override(self):
        """Some CLI args override, others preserve from config."""
        config = {
            "output_dir": "yaml_output",
            "default_count": 4,
            "aspect_ratio": "1:1",
            "model": "auto",
        }
        args = parse_args(["--output-dir", "cli_output", "--count", "3"])

        merged = merge_config(config, args)

        assert merged["output_dir"] == "cli_output"
        assert merged["default_count"] == 3
        assert merged["aspect_ratio"] == "1:1"  # Preserved from config
        assert merged["model"] == "auto"  # Preserved from config

    def test_merge_config_no_cli_args(self):
        """No CLI args means config is preserved."""
        config = {"output_dir": "yaml_output", "default_count": 4}
        args = parse_args([])

        merged = merge_config(config, args)

        assert merged["output_dir"] == "yaml_output"
        assert merged["default_count"] == 4

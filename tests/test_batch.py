"""Tests for batch file parsing functionality."""

import pytest
import os
from src.config import parse_batch_file


@pytest.fixture
def fixtures_dir():
    """Return path to test fixtures directory."""
    return os.path.join(os.path.dirname(__file__), "fixtures")


class TestParseTxt:
    """Tests for .txt batch file parsing."""

    def test_parse_txt_returns_correct_count(self, fixtures_dir):
        """Parse sample_prompts.txt should return exactly 3 prompts."""
        path = os.path.join(fixtures_dir, "sample_prompts.txt")
        result = parse_batch_file(path)
        assert len(result) == 3

    def test_parse_txt_skips_comments(self, fixtures_dir):
        """No result should have prompt starting with #."""
        path = os.path.join(fixtures_dir, "sample_prompts.txt")
        result = parse_batch_file(path)
        for item in result:
            assert not item["prompt"].startswith("#")

    def test_parse_txt_skips_empty_lines(self, fixtures_dir):
        """No result should have empty prompt string."""
        path = os.path.join(fixtures_dir, "sample_prompts.txt")
        result = parse_batch_file(path)
        for item in result:
            assert item["prompt"].strip() != ""

    def test_parse_txt_prompt_has_prompt_key(self, fixtures_dir):
        """Each result dict should have 'prompt' key."""
        path = os.path.join(fixtures_dir, "sample_prompts.txt")
        result = parse_batch_file(path)
        for item in result:
            assert isinstance(item, dict)
            assert "prompt" in item

    def test_parse_txt_whitespace_stripped(self, fixtures_dir):
        """Leading/trailing spaces should be removed from prompts."""
        path = os.path.join(fixtures_dir, "sample_prompts.txt")
        result = parse_batch_file(path)
        for item in result:
            # Check that there's no leading/trailing whitespace
            assert item["prompt"] == item["prompt"].strip()


class TestParseJson:
    """Tests for .json batch file parsing."""

    def test_parse_json_objects(self, fixtures_dir):
        """Parse sample_prompts.json (object array) → 3 dicts with 'prompt' key."""
        path = os.path.join(fixtures_dir, "sample_prompts.json")
        result = parse_batch_file(path)
        assert len(result) == 3
        for item in result:
            assert isinstance(item, dict)
            assert "prompt" in item

    def test_parse_json_objects_preserve_fields(self, fixtures_dir):
        """JSON objects should preserve optional fields like 'count', 'aspect_ratio', 'model'."""
        path = os.path.join(fixtures_dir, "sample_prompts.json")
        result = parse_batch_file(path)

        # First item should have count and aspect_ratio
        assert result[0]["count"] == 2
        assert result[0]["aspect_ratio"] == "16:9"

        # Second item should have count but no aspect_ratio
        assert result[1]["count"] == 4
        assert "aspect_ratio" not in result[1]

        # Third item should have aspect_ratio and model but no count
        assert result[2]["aspect_ratio"] == "9:16"
        assert result[2]["model"] == "auto"

    def test_parse_json_simple_array(self, fixtures_dir):
        """Parse simple_prompts.json (string array) → 3 dicts with 'prompt' key."""
        path = os.path.join(fixtures_dir, "simple_prompts.json")
        result = parse_batch_file(path)
        assert len(result) == 3
        assert result[0]["prompt"] == "A red sunset"
        assert result[1]["prompt"] == "A blue ocean"
        assert result[2]["prompt"] == "A green forest"


class TestErrorHandling:
    """Tests for error handling in batch file parsing."""

    def test_parse_nonexistent_file(self):
        """FileNotFoundError should be raised for missing file."""
        with pytest.raises(FileNotFoundError):
            parse_batch_file("/nonexistent/path/file.txt")

    def test_parse_unsupported_extension(self, fixtures_dir):
        """ValueError should be raised for unsupported file format."""
        # Create a dummy .csv file temporarily
        csv_path = os.path.join(fixtures_dir, "dummy.csv")
        open(csv_path, "w").close()
        try:
            with pytest.raises(ValueError, match="Unsupported batch file format"):
                parse_batch_file(csv_path)
        finally:
            os.remove(csv_path)

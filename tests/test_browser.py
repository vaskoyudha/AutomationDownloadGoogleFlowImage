import os
import importlib
from unittest.mock import patch

from src.browser import BrowserManager

pytest = importlib.import_module("pytest")


class TestFindChromeProfile:
    def test_explicit_path_valid(self, tmp_path):
        profile_dir = tmp_path / "TestProfile"
        profile_dir.mkdir()
        bm = BrowserManager({"chrome_profile_path": str(profile_dir)})
        result = bm._find_chrome_profile()
        assert result == str(profile_dir)

    def test_explicit_path_invalid_raises(self):
        bm = BrowserManager({"chrome_profile_path": "/nonexistent/path/Default"})
        with pytest.raises(RuntimeError, match="not found"):
            bm._find_chrome_profile()

    def test_auto_detect_found(self, tmp_path):
        fake_profile = tmp_path / "Default"
        fake_profile.mkdir()
        with patch("src.browser.CHROME_PROFILE_PATHS", [str(fake_profile)]):
            bm = BrowserManager({})
            result = bm._find_chrome_profile()
            assert result == str(fake_profile)

    def test_auto_detect_not_found_raises_helpful_error(self):
        with patch(
            "src.browser.CHROME_PROFILE_PATHS", ["/nonexistent1", "/nonexistent2"]
        ):
            bm = BrowserManager({})
            with pytest.raises(RuntimeError) as exc_info:
                bm._find_chrome_profile()
            error_msg = str(exc_info.value)
            assert "Chrome" in error_msg
            assert "Install" in error_msg or "install" in error_msg


class TestCopyProfileToTemp:
    def test_copy_creates_temp_dir(self, tmp_path):
        src_profile = tmp_path / "SourceProfile"
        src_profile.mkdir()
        (src_profile / "test_file.txt").write_text("test data")

        bm = BrowserManager({})
        dest = bm._copy_profile_to_temp(str(src_profile))

        assert os.path.isdir(dest)
        assert os.path.exists(os.path.join(dest, "test_file.txt"))

        bm._cleanup_temp_profile()

    def test_copy_original_untouched(self, tmp_path):
        src_profile = tmp_path / "SourceProfile"
        src_profile.mkdir()
        (src_profile / "original.txt").write_text("original")

        bm = BrowserManager({})
        bm._copy_profile_to_temp(str(src_profile))

        assert (src_profile / "original.txt").read_text() == "original"

        bm._cleanup_temp_profile()

    def test_cleanup_removes_temp(self, tmp_path):
        src_profile = tmp_path / "SourceProfile"
        src_profile.mkdir()

        bm = BrowserManager({})
        bm._copy_profile_to_temp(str(src_profile))
        temp_dir = bm._temp_profile_dir

        assert temp_dir is not None
        assert os.path.isdir(temp_dir)
        bm._cleanup_temp_profile()
        assert not os.path.isdir(temp_dir)

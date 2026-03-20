import asyncio
import os
from pathlib import Path
from unittest.mock import patch

from src.downloader import ImageDownloader, RequestProtocol


def test_build_save_path_index_001() -> None:
    downloader = ImageDownloader({"output_dir": "output"})
    path = downloader.build_save_path("output", "sunset", "2026-03-20", 1, "png")
    assert path == os.path.join("output", "sunset", "sunset_2026-03-20_001.png")


def test_build_save_path_index_099() -> None:
    downloader = ImageDownloader({"output_dir": "output"})
    path = downloader.build_save_path("output", "sunset", "2026-03-20", 99, "png")
    assert path == os.path.join("output", "sunset", "sunset_2026-03-20_099.png")


def test_build_save_path_index_999() -> None:
    downloader = ImageDownloader({"output_dir": "output"})
    path = downloader.build_save_path("output", "sunset", "2026-03-20", 999, "png")
    assert path == os.path.join("output", "sunset", "sunset_2026-03-20_999.png")


def test_detect_image_format_png() -> None:
    downloader = ImageDownloader({"output_dir": "output"})
    assert downloader.detect_image_format(b"\x89PNG\r\n\x1a\nrest") == "png"


def test_detect_image_format_jpeg() -> None:
    downloader = ImageDownloader({"output_dir": "output"})
    assert downloader.detect_image_format(b"\xff\xd8\xffrest") == "jpeg"


def test_detect_image_format_webp() -> None:
    downloader = ImageDownloader({"output_dir": "output"})
    assert downloader.detect_image_format(b"RIFF\x00\x00\x00\x00WEBP") == "webp"


def test_detect_image_format_unknown_defaults_to_png() -> None:
    downloader = ImageDownloader({"output_dir": "output"})
    assert downloader.detect_image_format(b"GIF89a") == "png"


def test_duplicate_filename_handling_increments_index_for_strategy1(
    tmp_path: Path,
) -> None:
    downloader = ImageDownloader({"output_dir": str(tmp_path)})

    class MockResponse:
        async def body(self) -> bytes:
            return b"\x89PNG\r\n\x1a\nabc"

    class MockRequest:
        async def get(self, url: str) -> MockResponse:
            _ = url
            return MockResponse()

    class MockPage:
        def __init__(self) -> None:
            self.request: RequestProtocol = MockRequest()

        def expect_download(self):
            raise RuntimeError("unused")

        async def query_selector(self, selector: str):
            _ = selector
            return None

    class MockImageElement:
        async def get_attribute(self, name: str) -> str:
            _ = name
            return "http://example.com/image"

        async def query_selector(self, selector: str) -> None:
            _ = selector
            return None

        async def screenshot(self) -> bytes:
            return b"\x89PNG\r\n\x1a\nabc"

        async def click(self) -> None:
            return None

    image_element = MockImageElement()

    def fake_exists(path: str) -> bool:
        return path.endswith("sunset_2026-03-20_001.png")

    with patch("src.downloader.os.path.exists", side_effect=fake_exists):
        path = asyncio.run(
            downloader.download_single_image(
                page=MockPage(),
                image_element=image_element,
                index=1,
                slug="sunset",
                date_str="2026-03-20",
            )
        )

    assert path.endswith("sunset_2026-03-20_002.png")

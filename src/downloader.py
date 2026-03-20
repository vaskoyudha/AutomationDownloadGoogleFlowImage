"""Image downloader for Google Flow generated images.

Handles image detection, multiple download strategies,
organized saving with naming conventions, and format detection.
"""

from __future__ import annotations

import datetime
import logging
import os
from collections.abc import Awaitable
from types import TracebackType
from typing import Protocol

from src.selectors import FlowSelectors
from src.utils import sanitize_prompt, ensure_output_dir


logger = logging.getLogger("flow_automation")


class ResponseProtocol(Protocol):
    async def body(self) -> bytes: ...


class RequestProtocol(Protocol):
    async def get(self, url: str) -> ResponseProtocol: ...


class DownloadProtocol(Protocol):
    suggested_filename: str

    async def save_as(self, path: str) -> None: ...


class DownloadInfoProtocol(Protocol):
    value: Awaitable[DownloadProtocol]


class ExpectDownloadContextProtocol(Protocol):
    async def __aenter__(self) -> DownloadInfoProtocol: ...

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> bool | None: ...


class ElementProtocol(Protocol):
    async def get_attribute(self, name: str) -> str | None: ...

    async def query_selector(self, selector: str) -> "ElementProtocol | None": ...

    async def click(self) -> None: ...

    async def screenshot(self) -> bytes: ...


class PageProtocol(Protocol):
    request: RequestProtocol

    def expect_download(self) -> ExpectDownloadContextProtocol: ...

    async def query_selector(self, selector: str) -> ElementProtocol | None: ...


class FlowProtocol(Protocol):
    async def get_generated_images(self) -> list[ElementProtocol]: ...


class ImageDownloader:
    def __init__(self, config: dict[str, object]):
        self.config: dict[str, object] = config or {}
        self.output_dir: str
        self.output_dir = str(self.config.get("output_dir", "output"))

    async def download_all_images(
        self, page: PageProtocol, flow: FlowProtocol, prompt: str
    ) -> list[str]:
        image_elements = await flow.get_generated_images()
        slug = sanitize_prompt(prompt)
        date_str = datetime.date.today().strftime("%Y-%m-%d")

        saved_paths: list[str] = []
        for index, image_element in enumerate(image_elements, start=1):
            path = await self._download_single_image(
                page=page,
                image_element=image_element,
                index=index,
                slug=slug,
                date_str=date_str,
            )
            saved_paths.append(path)

        return saved_paths

    async def _download_single_image(
        self,
        page: PageProtocol,
        image_element: ElementProtocol,
        index: int,
        slug: str,
        date_str: str,
    ) -> str:
        _ = ensure_output_dir(self.output_dir, slug)

        try:
            src = await image_element.get_attribute("src")
            if src and (src.startswith("http") or src.startswith("blob:")):
                response = await page.request.get(src)
                data = bytes(await response.body())
                if data:
                    ext = self._detect_image_format(data)
                    save_path = self._build_save_path(
                        self.output_dir, slug, date_str, index, ext
                    )
                    while os.path.exists(save_path):
                        index += 1
                        save_path = self._build_save_path(
                            self.output_dir, slug, date_str, index, ext
                        )

                    with open(save_path, "wb") as f:
                        _ = f.write(data)

                    logger.info("Image %s saved via src fetch: %s", index, save_path)
                    return save_path
        except Exception as exc:
            logger.debug("Strategy 1 failed for image %s: %s", index, exc)

        try:
            download_button = await image_element.query_selector(
                FlowSelectors.IMAGE_DOWNLOAD_BUTTON.css
            )

            if not download_button:
                menu_button = await image_element.query_selector(
                    FlowSelectors.IMAGE_DOWNLOAD_MENU.css
                )
                if menu_button:
                    await menu_button.click()
                    download_button = await page.query_selector(
                        FlowSelectors.IMAGE_DOWNLOAD_BUTTON.css
                    )

            if not download_button:
                download_button = await page.query_selector(
                    FlowSelectors.IMAGE_DOWNLOAD_BUTTON.css
                )

            if download_button:
                async with page.expect_download() as download_info:
                    await download_button.click()

                download = await download_info.value
                suggested_name = getattr(download, "suggested_filename", "") or ""
                ext = os.path.splitext(suggested_name)[1].lower().lstrip(".") or "png"

                save_path = self._build_save_path(
                    self.output_dir, slug, date_str, index, ext
                )
                while os.path.exists(save_path):
                    index += 1
                    save_path = self._build_save_path(
                        self.output_dir, slug, date_str, index, ext
                    )

                await download.save_as(save_path)
                logger.info("Image %s saved via browser download: %s", index, save_path)
                return save_path
        except Exception as exc:
            logger.debug("Strategy 2 failed for image %s: %s", index, exc)

        data = bytes(await image_element.screenshot())
        ext = "png"
        save_path = self._build_save_path(self.output_dir, slug, date_str, index, ext)
        while os.path.exists(save_path):
            index += 1
            save_path = self._build_save_path(
                self.output_dir, slug, date_str, index, ext
            )

        with open(save_path, "wb") as f:
            _ = f.write(data)

        logger.info("Image %s saved via element screenshot: %s", index, save_path)
        return save_path

    async def download_single_image(
        self,
        page: PageProtocol,
        image_element: ElementProtocol,
        index: int,
        slug: str,
        date_str: str,
    ) -> str:
        return await self._download_single_image(
            page=page,
            image_element=image_element,
            index=index,
            slug=slug,
            date_str=date_str,
        )

    def build_save_path(
        self,
        base_dir: str,
        slug: str,
        date_str: str,
        index: int,
        ext: str,
    ) -> str:
        return self._build_save_path(base_dir, slug, date_str, index, ext)

    @staticmethod
    def detect_image_format(data: bytes) -> str:
        return ImageDownloader._detect_image_format(data)

    def _build_save_path(
        self,
        base_dir: str,
        slug: str,
        date_str: str,
        index: int,
        ext: str,
    ) -> str:
        filename = f"{slug}_{date_str}_{index:03d}.{ext}"
        return os.path.join(base_dir, slug, filename)

    @staticmethod
    def _detect_image_format(data: bytes) -> str:
        if data.startswith(b"\x89PNG\r\n\x1a\n"):
            return "png"
        if data.startswith(b"\xff\xd8\xff"):
            return "jpeg"
        if len(data) >= 12 and data[0:4] == b"RIFF" and data[8:12] == b"WEBP":
            return "webp"
        return "png"

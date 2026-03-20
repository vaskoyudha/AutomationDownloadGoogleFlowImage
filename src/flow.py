"""Google Flow page interaction layer.

Handles navigation, prompt entry, settings configuration,
generation triggering, and result detection on labs.google/flow.
"""

from __future__ import annotations

import asyncio
import logging
import random
from typing import Protocol, TypedDict

from src.selectors import FlowSelectors, Selector
from src.utils import human_delay, retry_with_backoff


logger = logging.getLogger("flow_automation")
RETRY_PATTERN = retry_with_backoff


class FlowPage:
    def __init__(
        self,
        page: "PageProtocol",
        selectors: type[FlowSelectors] | None,
        config: dict[str, object] | None,
    ) -> None:
        self.page: PageProtocol = page
        self.selectors: type[FlowSelectors] = selectors or FlowSelectors
        self.config: dict[str, object] = config or {}

    def _int_config(self, primary_key: str, fallback_key: str, default: int) -> int:
        value = self.config.get(primary_key, self.config.get(fallback_key, default))
        if isinstance(value, bool):
            return int(value)
        if isinstance(value, (int, float, str)):
            try:
                return int(value)
            except ValueError:
                return default
        return default

    def _human_click_delay(self) -> None:
        human_delay(
            self._int_config("click_delay_min_ms", "click_delay_min", 200),
            self._int_config("click_delay_max_ms", "click_delay_max", 500),
        )

    def _typing_delay(self) -> int:
        min_delay = self._int_config("typing_speed_min_ms", "typing_speed_min", 50)
        max_delay = self._int_config("typing_speed_max_ms", "typing_speed_max", 150)
        if min_delay > max_delay:
            min_delay, max_delay = max_delay, min_delay
        return random.randint(min_delay, max_delay)

    async def _type_text(self, text: str) -> None:
        self._human_click_delay()
        await self.page.keyboard.type(text, delay=self._typing_delay())

    async def _query_with_fallback(
        self, selector_obj: Selector
    ) -> "ElementProtocol | None":
        element = await self.page.query_selector(selector_obj.css)
        if element:
            return element

        if selector_obj.aria:
            element = await self.page.query_selector(
                f"[aria-label*='{selector_obj.aria}']"
            )
            if element:
                return element

        if selector_obj.text:
            element = await self.page.query_selector(f"text={selector_obj.text}")
            if element:
                return element

        return None

    async def _click_selector(self, selector_obj: Selector) -> bool:
        element = await self._query_with_fallback(selector_obj)
        if not element:
            return False
        self._human_click_delay()
        await element.click()
        return True

    async def navigate(self) -> None:
        self._human_click_delay()
        await self.page.goto("https://labs.google/flow", wait_until="domcontentloaded")
        await self.dismiss_consent()

    async def dismiss_consent(self) -> None:
        try:
            _ = await self._click_selector(self.selectors.CONSENT_ACCEPT_BUTTON)
        except Exception:
            return

    async def enter_prompt(self, prompt: str) -> None:
        prompt_input = await self._query_with_fallback(self.selectors.PROMPT_INPUT)
        if not prompt_input:
            prompt_input = await self._query_with_fallback(
                self.selectors.PROMPT_TEXTAREA
            )
        if not prompt_input:
            raise RuntimeError("Prompt input not found")

        self._human_click_delay()
        await prompt_input.click()
        self._human_click_delay()
        await self.page.keyboard.press("Control+A")
        self._human_click_delay()
        await self.page.keyboard.press("Backspace")
        await self._type_text(prompt)

    async def configure_settings(
        self,
        count: int | None = None,
        aspect_ratio: str | None = None,
        model: str | None = None,
    ) -> None:
        if count is None and aspect_ratio is None and model is None:
            return

        try:
            opened = await self._click_selector(self.selectors.SETTINGS_PANEL_TRIGGER)
            if not opened:
                logger.warning(
                    "Settings panel trigger not found; continuing without setting changes"
                )
                return

            if model is not None:
                model_selector = await self._query_with_fallback(
                    self.selectors.MODEL_SELECTOR
                )
                if model_selector:
                    self._human_click_delay()
                    await model_selector.click()
                    await self._type_text(str(model))
                    self._human_click_delay()
                    await self.page.keyboard.press("Enter")
                else:
                    logger.warning(
                        "Model selector not found; skipping model configuration"
                    )

            if aspect_ratio is not None:
                aspect_selector = await self._query_with_fallback(
                    self.selectors.ASPECT_RATIO_SELECTOR
                )
                if aspect_selector:
                    self._human_click_delay()
                    await aspect_selector.click()
                    await self._type_text(str(aspect_ratio))
                    self._human_click_delay()
                    await self.page.keyboard.press("Enter")
                else:
                    logger.warning(
                        "Aspect ratio selector not found; skipping aspect ratio configuration"
                    )

            if count is not None:
                count_selector = await self._query_with_fallback(
                    self.selectors.IMAGE_COUNT_SELECTOR
                )
                if count_selector:
                    self._human_click_delay()
                    await count_selector.click()
                    self._human_click_delay()
                    await self.page.keyboard.press("Control+A")
                    self._human_click_delay()
                    await self.page.keyboard.press("Backspace")
                    await self._type_text(str(count))
                    self._human_click_delay()
                    await self.page.keyboard.press("Enter")
                else:
                    logger.warning(
                        "Image count selector not found; skipping count configuration"
                    )
        except Exception as exc:
            logger.warning(
                "Settings interaction unavailable (likely auth-gated): %s", exc
            )

    async def click_generate(self) -> None:
        clicked = await self._click_selector(self.selectors.GENERATE_BUTTON)
        if not clicked:
            clicked = await self._click_selector(self.selectors.CREATE_BUTTON)
        if not clicked:
            raise RuntimeError("Generate/Create button not found")

    async def _inter_generation_delay(self) -> None:
        base_seconds = self._int_config(
            "delay_between_generations", "delay_between_generations", 10
        )
        base_ms = max(0, base_seconds * 1000)
        min_ms = int(base_ms * 0.7)
        max_ms = int(base_ms * 1.3)
        if min_ms > max_ms:
            min_ms, max_ms = max_ms, min_ms
        human_delay(min_ms, max_ms)

    async def generate_with_resilience(
        self, prompt: str, settings: "GenerationSettings"
    ) -> bool:
        max_retries = max(1, self._int_config("max_retries", "max_retries", 3))
        quota_wait_time = max(
            0, self._int_config("quota_wait_time", "quota_wait_time", 60)
        )
        base_backoff: float = float(
            max(1, self._int_config("retry_base_delay", "retry_base_delay", 2))
        )

        await self.enter_prompt(prompt)
        if settings:
            await self.configure_settings(**settings)

        attempt = 0
        while attempt < max_retries:
            try:
                if attempt > 0:
                    await self._inter_generation_delay()

                await self.click_generate()

                if await self.detect_captcha():
                    logger.warning(
                        "CAPTCHA detected during generation; waiting for manual solve"
                    )
                    await self.handle_captcha()
                    await self.click_generate()

                if await self.detect_safety_filter():
                    logger.warning("Safety filter detected for prompt; skipping prompt")
                    return False

                if await self.detect_quota_exceeded():
                    logger.warning(
                        "Quota exceeded detected; waiting %ss before retry",
                        quota_wait_time,
                    )
                    if attempt >= max_retries - 1:
                        return False
                    await asyncio.sleep(quota_wait_time)
                    attempt += 1
                    continue

                if await self.wait_for_generation():
                    return True

                if attempt >= max_retries - 1:
                    return False

                backoff = base_backoff * (2.0**attempt)
                logger.warning(
                    "Generation did not complete; retrying in %.1fs (attempt %s/%s)",
                    backoff,
                    attempt + 1,
                    max_retries,
                )
                await asyncio.sleep(backoff)
                attempt += 1
            except KeyboardInterrupt:
                raise
            except Exception as exc:
                if attempt >= max_retries - 1:
                    logger.warning("Generation failed after retries: %s", exc)
                    return False
                backoff = base_backoff * (2.0**attempt)
                logger.warning(
                    "Generation attempt failed (%s); retrying in %.1fs", exc, backoff
                )
                await asyncio.sleep(backoff)
                attempt += 1

        return False

    async def wait_for_generation(self, timeout: int | None = None) -> bool:
        timeout_s = timeout
        if timeout_s is None:
            timeout_s = self._int_config(
                "generation_timeout", "generation_timeout", 120
            )
        timeout_ms = int(timeout_s * 1000)

        try:
            _ = await self.page.wait_for_selector(
                self.selectors.LOADING_INDICATOR.css, timeout=10000
            )
            _ = await self.page.wait_for_selector(
                self.selectors.LOADING_INDICATOR.css,
                state="hidden",
                timeout=timeout_ms,
            )
        except Exception:
            pass

        try:
            _ = await self.page.wait_for_selector(
                self.selectors.GENERATION_COMPLETE_SIGNAL.css,
                timeout=timeout_ms,
            )
            return True
        except Exception:
            images = await self.get_generated_images()
            return len(images) > 0

    async def detect_captcha(self) -> bool:
        captcha = await self.page.query_selector(self.selectors.CAPTCHA_OVERLAY.css)
        return captcha is not None

    async def handle_captcha(self) -> None:
        if not await self.detect_captcha():
            return
        print(
            "⚠️ CAPTCHA detected! Please solve it in the browser window. Press Enter when done..."
        )
        _ = input()
        if await self.detect_captcha():
            raise RuntimeError("CAPTCHA still present after manual solve confirmation")

    async def detect_safety_filter(self) -> bool:
        warning = await self.page.query_selector(
            self.selectors.SAFETY_FILTER_WARNING.css
        )
        return warning is not None

    async def detect_quota_exceeded(self) -> bool:
        dialog = await self.page.query_selector(
            self.selectors.QUOTA_EXCEEDED_DIALOG.css
        )
        return dialog is not None

    async def get_generated_images(self) -> list["ElementProtocol"]:
        return await self.page.query_selector_all(
            self.selectors.GENERATED_IMAGE_ITEM.css
        )


class ElementProtocol(Protocol):
    async def click(self) -> None: ...


class KeyboardProtocol(Protocol):
    async def type(self, text: str, delay: int) -> None: ...

    async def press(self, key: str) -> None: ...


class PageProtocol(Protocol):
    keyboard: KeyboardProtocol

    async def goto(self, url: str, wait_until: str) -> None: ...

    async def query_selector(self, selector: str) -> ElementProtocol | None: ...

    async def query_selector_all(self, selector: str) -> list[ElementProtocol]: ...

    async def wait_for_selector(
        self,
        selector: str,
        timeout: int,
        state: str | None = None,
    ) -> ElementProtocol | None: ...


class GenerationSettings(TypedDict, total=False):
    count: int
    aspect_ratio: str
    model: str

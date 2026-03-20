import asyncio
from typing import cast
from unittest.mock import AsyncMock, patch

from src.flow import FlowPage
from src.utils import human_delay, retry_with_backoff


def test_retry_with_backoff_succeeds_on_third_try() -> None:
    attempts = {"count": 0}

    @retry_with_backoff(max_retries=3, base_delay=0)
    def flaky() -> str:
        attempts["count"] += 1
        if attempts["count"] < 3:
            raise RuntimeError("retry")
        return "ok"

    result = cast(str, flaky())

    assert result == "ok"
    assert attempts["count"] == 3


def test_human_delay_uses_random_value_within_range() -> None:
    with (
        patch("src.utils.random.uniform", return_value=0.123) as uniform_mock,
        patch("src.utils.time.sleep") as sleep_mock,
    ):
        human_delay(100, 200)

    uniform_mock.assert_called_once_with(0.1, 0.2)
    sleep_mock.assert_called_once_with(0.123)


def test_generate_with_resilience_returns_false_on_safety_filter() -> None:
    flow = FlowPage(page=AsyncMock(), selectors=None, config={"max_retries": 3})
    flow.enter_prompt = AsyncMock()
    flow.configure_settings = AsyncMock()
    flow.click_generate = AsyncMock()
    flow.detect_captcha = AsyncMock(return_value=False)
    flow.handle_captcha = AsyncMock()
    flow.detect_safety_filter = AsyncMock(return_value=True)
    flow.detect_quota_exceeded = AsyncMock(return_value=False)
    flow.wait_for_generation = AsyncMock(return_value=True)

    result = asyncio.run(flow.generate_with_resilience("test prompt", {"count": 2}))

    assert result is False
    flow.enter_prompt.assert_awaited_once_with("test prompt")
    flow.configure_settings.assert_awaited_once_with(count=2)
    flow.click_generate.assert_awaited_once()
    flow.detect_safety_filter.assert_awaited_once()
    flow.wait_for_generation.assert_not_awaited()


def test_generate_with_resilience_success_path_returns_true() -> None:
    flow = FlowPage(page=AsyncMock(), selectors=None, config={"max_retries": 3})
    flow.enter_prompt = AsyncMock()
    flow.configure_settings = AsyncMock()
    flow.click_generate = AsyncMock()
    flow.detect_captcha = AsyncMock(return_value=False)
    flow.handle_captcha = AsyncMock()
    flow.detect_safety_filter = AsyncMock(return_value=False)
    flow.detect_quota_exceeded = AsyncMock(return_value=False)
    flow.wait_for_generation = AsyncMock(return_value=True)

    result = asyncio.run(flow.generate_with_resilience("test prompt", {}))

    assert result is True
    flow.enter_prompt.assert_awaited_once_with("test prompt")
    flow.configure_settings.assert_not_awaited()
    flow.wait_for_generation.assert_awaited_once()


def test_generate_with_resilience_retries_on_generation_timeout() -> None:
    flow = FlowPage(page=AsyncMock(), selectors=None, config={"max_retries": 3})
    flow.enter_prompt = AsyncMock()
    flow.configure_settings = AsyncMock()
    flow.click_generate = AsyncMock()
    flow.detect_captcha = AsyncMock(return_value=False)
    flow.handle_captcha = AsyncMock()
    flow.detect_safety_filter = AsyncMock(return_value=False)
    flow.detect_quota_exceeded = AsyncMock(return_value=False)
    flow.wait_for_generation = AsyncMock(side_effect=[False, False, False])
    with patch("src.flow.asyncio.sleep", new=AsyncMock()) as sleep_mock:
        result = asyncio.run(flow.generate_with_resilience("retry prompt", {}))

    assert result is False
    assert flow.click_generate.await_count == 3
    assert flow.wait_for_generation.await_count == 3
    assert sleep_mock.await_args_list[0].args[0] == 2.0
    assert sleep_mock.await_args_list[1].args[0] == 4.0


def test_generate_with_resilience_applies_inter_generation_jitter() -> None:
    flow = FlowPage(page=AsyncMock(), selectors=None, config={"max_retries": 2})
    flow.enter_prompt = AsyncMock()
    flow.configure_settings = AsyncMock()
    flow.click_generate = AsyncMock()
    flow.detect_captcha = AsyncMock(return_value=False)
    flow.handle_captcha = AsyncMock()
    flow.detect_safety_filter = AsyncMock(return_value=False)
    flow.detect_quota_exceeded = AsyncMock(return_value=False)
    flow.wait_for_generation = AsyncMock(side_effect=[False, True])

    with (
        patch("src.flow.human_delay") as delay_mock,
        patch("src.flow.asyncio.sleep", new=AsyncMock()),
    ):
        result = asyncio.run(flow.generate_with_resilience("retry prompt", {}))

    assert result is True
    assert delay_mock.call_count >= 1
    assert delay_mock.call_args_list[-1].args == (7000, 13000)

"""Browser session manager for Google Flow automation.

Handles Chrome profile copying, Playwright persistent context launch,
and browser lifecycle management.
"""

import logging
import os
import shutil
import tempfile
import importlib
from typing import Any, Optional


logger = logging.getLogger("flow_automation")

CHROME_PROFILE_PATHS = [
    os.path.expanduser("~/.config/google-chrome/Default"),
    os.path.expanduser("~/.config/chromium/Default"),
    os.path.expanduser("~/.config/google-chrome-beta/Default"),
    os.path.expanduser("~/snap/google-chrome/current/.config/google-chrome/Default"),
]


class BrowserManager:
    """Manages Chrome browser session for Google Flow automation.

    Copies Chrome profile to temp dir to avoid lock conflicts,
    then launches Playwright with persistent context for login state reuse.
    """

    def __init__(self, config: dict[str, Any]):
        """Initialize BrowserManager with configuration.

        Args:
            config: Configuration dict with optional keys:
                - chrome_profile_path: Override auto-detected Chrome profile path
                - headless: Run in headless mode (default: False)
        """
        self.config = config
        self.headless = config.get("headless", False)
        self.use_cdp = config.get("use_cdp", False)
        self.chrome_profile_path = config.get("chrome_profile_path")
        self._temp_profile_dir: Optional[str] = None
        self._playwright = None
        self._context = None

    def _find_chrome_profile(self) -> str:
        """Auto-detect Chrome profile directory.

        Returns the path to the first found Chrome profile.
        Raises RuntimeError with helpful message if none found.
        """
        if self.chrome_profile_path:
            if os.path.isdir(self.chrome_profile_path):
                return self.chrome_profile_path
            raise RuntimeError(
                f"Configured Chrome profile path not found: {self.chrome_profile_path}\n"
                "Please check your config.yaml chrome_profile_path setting."
            )

        for path in CHROME_PROFILE_PATHS:
            if os.path.isdir(path):
                logger.info("Found Chrome profile at: %s", path)
                return path

        raise RuntimeError(
            "Chrome profile not found. Please:\n"
            "1. Install Google Chrome: https://www.google.com/chrome/\n"
            "2. Launch Chrome and log into your Google account\n"
            "3. Navigate to labs.google/flow and accept any terms\n"
            "4. Close Chrome completely\n"
            "5. Re-run this tool\n\n"
            f"Searched paths:\n" + "\n".join(f"  - {p}" for p in CHROME_PROFILE_PATHS)
        )

    def _find_chrome_profile_path(self) -> Optional[str]:
        if self.chrome_profile_path and os.path.isdir(self.chrome_profile_path):
            return self.chrome_profile_path
        for path in CHROME_PROFILE_PATHS:
            if os.path.isdir(path):
                return path
        return None

    def _copy_profile_to_temp(self, profile_path: str) -> str:
        """Copy Chrome profile to a temporary directory.

        This avoids lock conflicts when Chrome is open while automation runs.
        The original profile is never modified.

        Args:
            profile_path: Source Chrome profile directory path

        Returns:
            Path to the temporary profile copy
        """
        self._temp_profile_dir = tempfile.mkdtemp(prefix="flow_chrome_profile_")
        dest = os.path.join(self._temp_profile_dir, "Default")
        logger.info("Copying Chrome profile from %s to %s", profile_path, dest)
        shutil.copytree(profile_path, dest)
        logger.debug("Profile copied successfully to: %s", dest)
        return dest

    def _cleanup_temp_profile(self):
        """Remove temporary profile directory."""
        if self._temp_profile_dir and os.path.isdir(self._temp_profile_dir):
            shutil.rmtree(self._temp_profile_dir, ignore_errors=True)
            logger.debug("Cleaned up temp profile: %s", self._temp_profile_dir)
            self._temp_profile_dir = None

    def _sync_profile_back(self) -> None:
        """Sync session cookies from temp profile back to original Chrome profile.

        After interactive login, new cookies are written to the temp profile with
        basic (unencrypted) storage. Syncing them back means subsequent runs won't
        need interactive login.
        """
        if not self._temp_profile_dir:
            return
        original = self._find_chrome_profile_path()
        if not original or not os.path.isdir(original):
            return
        temp_default = os.path.join(self._temp_profile_dir, "Default")
        if not os.path.isdir(temp_default):
            return
        for filename in ("Cookies", "Cookies-journal", "Local State"):
            src = os.path.join(temp_default, filename)
            if os.path.isfile(src):
                dst = os.path.join(original, filename)
                try:
                    shutil.copy2(src, dst)
                    logger.debug("Synced %s back to original profile", filename)
                except Exception as exc:
                    logger.warning(
                        "Could not sync %s back to original profile: %s",
                        filename,
                        exc,
                    )

    async def launch(self):
        """Launch browser with Playwright persistent context.

        Returns:
            Tuple of (BrowserContext, Page)
        """
        async_playwright = importlib.import_module(
            "playwright.async_api"
        ).async_playwright

        if self.use_cdp:
            self._playwright = await async_playwright().start()
            browser = await self._playwright.chromium.connect_over_cdp(
                "http://localhost:9222"
            )
            if browser.contexts:
                self._context = browser.contexts[0]
            else:
                self._context = await browser.new_context()
            if self._context.pages:
                page = self._context.pages[0]
            else:
                page = await self._context.new_page()
            return self._context, page

        auth_state_path = os.path.join(
            os.path.dirname(__file__), "..", "auth_state.json"
        )
        if os.path.isfile(auth_state_path):
            self._playwright = await async_playwright().start()
            browser = await self._playwright.chromium.launch(
                headless=self.headless,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
                slow_mo=50,
            )
            self._context = await browser.new_context(
                storage_state=auth_state_path,
                viewport={"width": 1920, "height": 1080},
            )
            page = await self._context.new_page()
            return self._context, page

        profile_path = self._find_chrome_profile()
        self._copy_profile_to_temp(profile_path)
        user_data_dir = self._temp_profile_dir

        self._playwright = await async_playwright().start()

        try:
            self._context = await self._playwright.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                channel="chrome",
                headless=self.headless,
                viewport={"width": 1920, "height": 1080},
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--password-store=basic",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
                slow_mo=50,
            )
        except Exception as e:
            if "channel" in str(e) or "chrome" in str(e).lower():
                logger.warning("Chrome not found, falling back to Chromium...")
                self._context = (
                    await self._playwright.chromium.launch_persistent_context(
                        user_data_dir=user_data_dir,
                        headless=self.headless,
                        viewport={"width": 1920, "height": 1080},
                        args=[
                            "--disable-blink-features=AutomationControlled",
                            "--password-store=basic",
                            "--no-sandbox",
                            "--disable-setuid-sandbox",
                        ],
                        slow_mo=50,
                    )
                )
            else:
                raise

        if self._context.pages:
            page = self._context.pages[0]
        else:
            page = await self._context.new_page()

        return self._context, page

    async def close(self):
        """Close browser context and clean up temp profile."""
        if self._context:
            await self._context.close()
            self._context = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None
        self._sync_profile_back()
        self._cleanup_temp_profile()

    async def __aenter__(self):
        """Async context manager entry."""
        return await self.launch()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
        return False

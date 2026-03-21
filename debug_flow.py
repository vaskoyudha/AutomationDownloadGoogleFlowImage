#!/usr/bin/env python3
"""Debug script for Google Flow automation.

Launches a headed Chrome browser with the user's profile, navigates to
labs.google/fx/flow, takes a screenshot, and dumps DOM information to
understand the current UI structure and available selectors.
"""

import os
import shutil
import tempfile
import asyncio
from pathlib import Path


async def main():
    """Main debug flow."""
    from playwright.async_api import async_playwright

    # === Step 1: Copy Chrome profile to temp dir (same as browser.py) ===
    chrome_profile_path = os.path.expanduser("~/.config/google-chrome/Default")
    if not os.path.isdir(chrome_profile_path):
        print(f"ERROR: Chrome profile not found at {chrome_profile_path}")
        return

    temp_profile_dir = tempfile.mkdtemp(prefix="flow_chrome_profile_")
    dest_profile = os.path.join(temp_profile_dir, "Default")
    print(f"Copying Chrome profile from {chrome_profile_path} to {dest_profile}...")
    shutil.copytree(chrome_profile_path, dest_profile)
    print(f"Profile copied successfully.")

    try:
        # === Step 2: Launch visible Chrome with copied profile ===
        async with async_playwright() as p:
            print("Launching Chrome browser (headed)...")
            context = await p.chromium.launch_persistent_context(
                user_data_dir=temp_profile_dir,
                channel="chrome",
                headless=False,  # Visible browser
                viewport={"width": 1920, "height": 1080},
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--password-store=basic",
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                ],
            )

            # Get or create a page
            if context.pages:
                page = context.pages[0]
            else:
                page = await context.new_page()

            # === Step 3: Navigate to Flow app ===
            print("Navigating to https://labs.google/fx/tools/flow...")
            await page.goto(
                "https://labs.google/fx/tools/flow", wait_until="networkidle"
            )

            # === Step 4: Wait for page to load ===
            print("Waiting 5 seconds for page to fully load...")
            await page.wait_for_timeout(5000)

            # === Step 5: Take screenshot ===
            screenshot_path = "/tmp/flow_debug.png"
            await page.screenshot(path=screenshot_path)
            print(f"Screenshot saved to {screenshot_path}")

            # === Step 6: Print current URL ===
            current_url = page.url
            print(f"\n=== CURRENT URL ===")
            print(f"{current_url}")

            # === Step 7: Print HTML body (first 3000 chars) ===
            html_content = await page.evaluate("document.body.innerHTML")
            print(f"\n=== HTML BODY (first 3000 chars) ===")
            print(html_content[:3000])
            print(f"\n... (total length: {len(html_content)} chars) ...\n")

            # === Step 8: Query and print all interactive elements ===
            print(f"=== ALL INPUT ELEMENTS ===")
            inputs = await page.query_selector_all("input")
            for i, inp in enumerate(inputs):
                input_type = await inp.get_attribute("type") or "text"
                placeholder = await inp.get_attribute("placeholder") or ""
                aria_label = await inp.get_attribute("aria-label") or ""
                name = await inp.get_attribute("name") or ""
                data_testid = await inp.get_attribute("data-testid") or ""
                print(
                    f"  [{i}] type={input_type}, placeholder={placeholder!r}, "
                    f"aria-label={aria_label!r}, name={name!r}, data-testid={data_testid!r}"
                )

            print(f"\n=== ALL TEXTAREA ELEMENTS ===")
            textareas = await page.query_selector_all("textarea")
            for i, ta in enumerate(textareas):
                placeholder = await ta.get_attribute("placeholder") or ""
                aria_label = await ta.get_attribute("aria-label") or ""
                name = await ta.get_attribute("name") or ""
                data_testid = await ta.get_attribute("data-testid") or ""
                text_content = await ta.text_content() or ""
                print(
                    f"  [{i}] placeholder={placeholder!r}, aria-label={aria_label!r}, "
                    f"name={name!r}, data-testid={data_testid!r}, text={text_content[:50]!r}"
                )

            print(f"\n=== ALL BUTTON ELEMENTS ===")
            buttons = await page.query_selector_all("button")
            for i, btn in enumerate(buttons):
                aria_label = await btn.get_attribute("aria-label") or ""
                data_testid = await btn.get_attribute("data-testid") or ""
                text_content = await btn.text_content() or ""
                disabled = await btn.get_attribute("disabled")
                print(
                    f"  [{i}] aria-label={aria_label!r}, data-testid={data_testid!r}, "
                    f"text={text_content[:50]!r}, disabled={disabled}"
                )

            # === Step 9: Query elements with placeholders ===
            print(f"\n=== ELEMENTS WITH PLACEHOLDER ATTRIBUTE ===")
            placeholders = await page.query_selector_all("[placeholder]")
            for i, elem in enumerate(placeholders):
                tag = await page.evaluate("el => el.tagName", elem)
                placeholder = await elem.get_attribute("placeholder") or ""
                type_attr = await elem.get_attribute("type") or ""
                aria_label = await elem.get_attribute("aria-label") or ""
                print(
                    f"  [{i}] tag={tag}, placeholder={placeholder!r}, "
                    f"type={type_attr!r}, aria-label={aria_label!r}"
                )

            # === Step 10: Query elements with data-testid ===
            print(f"\n=== ELEMENTS WITH DATA-TESTID ATTRIBUTE ===")
            testids = await page.query_selector_all("[data-testid]")
            for i, elem in enumerate(testids):
                tag = await page.evaluate("el => el.tagName", elem)
                testid = await elem.get_attribute("data-testid") or ""
                aria_label = await elem.get_attribute("aria-label") or ""
                text_content = await elem.text_content() or ""
                print(
                    f"  [{i}] tag={tag}, data-testid={testid!r}, "
                    f"aria-label={aria_label!r}, text={text_content[:50]!r}"
                )

            # === Step 11: Query elements with aria-label ===
            print(f"\n=== ELEMENTS WITH ARIA-LABEL ATTRIBUTE ===")
            aria_labels = await page.query_selector_all("[aria-label]")
            for i, elem in enumerate(
                aria_labels[:30]
            ):  # Limit to first 30 to avoid spam
                tag = await page.evaluate("el => el.tagName", elem)
                aria_label = await elem.get_attribute("aria-label") or ""
                data_testid = await elem.get_attribute("data-testid") or ""
                text_content = await elem.text_content() or ""
                print(
                    f"  [{i}] tag={tag}, aria-label={aria_label!r}, "
                    f"data-testid={data_testid!r}, text={text_content[:50]!r}"
                )
            if len(aria_labels) > 30:
                print(f"  ... and {len(aria_labels) - 30} more aria-label elements")

            # === Step 12: Wait 3 more seconds ===
            print(f"\nWaiting 3 more seconds before closing...")
            await page.wait_for_timeout(3000)

            # === Step 13: Close ===
            print("Closing browser...")
            await context.close()

    finally:
        # Clean up temp profile
        print(f"Cleaning up temp profile at {temp_profile_dir}...")
        shutil.rmtree(temp_profile_dir, ignore_errors=True)
        print("Debug complete!")


if __name__ == "__main__":
    asyncio.run(main())

#!/usr/bin/env python3
"""Interactive selector discovery script for Google Flow (CDP mode).

This script uses Chrome's remote debugging endpoint so Chrome decrypts profile
cookies natively (including Ubuntu 24 portal-encrypted cookies).
"""

import asyncio
import json
import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request


CHROME_PROFILE = os.path.expanduser("~/.config/google-chrome/Default")
CHROME_BINARY = "google-chrome"
CDP_PORT = 9222
OUTPUT_TXT = "/tmp/flow_editor_dom.txt"
OUTPUT_PNG = "/tmp/flow_editor.png"
OUTPUT_JSON = "/tmp/flow_editor_selectors.json"


def is_port_open(port: int = CDP_PORT) -> bool:
    s = socket.socket()
    s.settimeout(1)
    try:
        s.connect(("localhost", port))
        return True
    except OSError:
        return False
    finally:
        s.close()


def wait_for_cdp(port: int = CDP_PORT, timeout: int = 10) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            _ = urllib.request.urlopen(f"http://localhost:{port}/json", timeout=2)
            return True
        except (urllib.error.URLError, TimeoutError, OSError):
            time.sleep(0.5)
    return False


def launch_chrome_if_needed() -> subprocess.Popen[bytes] | None:
    if is_port_open(CDP_PORT):
        print(f"Chrome already running with CDP on port {CDP_PORT}")
        return None

    user_data_dir = os.path.dirname(CHROME_PROFILE)
    profile_dir = os.path.basename(CHROME_PROFILE)
    chrome_proc = subprocess.Popen(
        [
            CHROME_BINARY,
            f"--remote-debugging-port={CDP_PORT}",
            f"--user-data-dir={user_data_dir}",
            f"--profile-directory={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
        ]
    )
    print(f"Chrome launched with --remote-debugging-port={CDP_PORT}")

    if not wait_for_cdp(timeout=10):
        print("ERROR: CDP port did not open in time")
        raise RuntimeError("CDP endpoint unavailable")

    return chrome_proc


async def wait_for_login(page) -> None:
    """Pause and wait for user to complete Google sign-in."""
    print("\n" + "=" * 60)
    print("⚠️  SIGN-IN REQUIRED")
    print("=" * 60)
    print("Please log into your Google account in the browser window.")
    print("After you have fully signed in, press Enter here to continue.")
    print("=" * 60)
    sys.stdout.flush()
    # We can't use asyncio.get_event_loop().run_in_executor here easily in a simple script,
    # so we just use blocking input() — the browser stays open
    input("Press Enter after logging in: ")
    print("Waiting for sign-in to complete (up to 60s)...")
    deadline = asyncio.get_running_loop().time() + 60
    while asyncio.get_running_loop().time() < deadline:
        if "accounts.google.com" not in page.url:
            print(f"✅ Sign-in complete. Current URL: {page.url}")
            return
        await asyncio.sleep(1)
    raise RuntimeError("Still on sign-in page after 60s. Did not detect redirect.")


async def dump_dom(page, label: str, out_lines: list[str]) -> None:
    """Dump detailed DOM info for the current page state."""
    url = page.url
    out_lines.append(f"\n{'=' * 70}")
    out_lines.append(f"SECTION: {label}")
    out_lines.append(f"URL: {url}")
    out_lines.append(f"{'=' * 70}")

    # All inputs
    inputs = await page.query_selector_all("input")
    out_lines.append(f"\n--- INPUT elements ({len(inputs)}) ---")
    for i, el in enumerate(inputs):
        attrs = await page.evaluate(
            """el => ({
            type: el.type,
            placeholder: el.placeholder,
            ariaLabel: el.getAttribute('aria-label'),
            name: el.name,
            id: el.id,
            className: el.className,
            dataTestId: el.getAttribute('data-testid'),
            role: el.getAttribute('role'),
            value: el.value ? el.value.slice(0, 50) : ''
        })""",
            el,
        )
        out_lines.append(f"  [{i}] {json.dumps(attrs)}")

    # All textareas
    textareas = await page.query_selector_all("textarea")
    out_lines.append(f"\n--- TEXTAREA elements ({len(textareas)}) ---")
    for i, el in enumerate(textareas):
        attrs = await page.evaluate(
            """el => ({
            placeholder: el.placeholder,
            ariaLabel: el.getAttribute('aria-label'),
            name: el.name,
            id: el.id,
            className: el.className,
            dataTestId: el.getAttribute('data-testid'),
            role: el.getAttribute('role'),
            textContent: el.textContent ? el.textContent.slice(0, 80) : ''
        })""",
            el,
        )
        out_lines.append(f"  [{i}] {json.dumps(attrs)}")

    # contenteditable divs
    editables = await page.query_selector_all("[contenteditable='true']")
    out_lines.append(f"\n--- contenteditable elements ({len(editables)}) ---")
    for i, el in enumerate(editables):
        attrs = await page.evaluate(
            """el => ({
            tagName: el.tagName,
            ariaLabel: el.getAttribute('aria-label'),
            id: el.id,
            className: el.className,
            dataTestId: el.getAttribute('data-testid'),
            role: el.getAttribute('role'),
            placeholder: el.getAttribute('placeholder'),
            textContent: el.textContent ? el.textContent.slice(0, 80) : ''
        })""",
            el,
        )
        out_lines.append(f"  [{i}] {json.dumps(attrs)}")

    # All buttons
    buttons = await page.query_selector_all("button")
    out_lines.append(f"\n--- BUTTON elements ({len(buttons)}) ---")
    for i, el in enumerate(buttons[:50]):  # cap at 50
        attrs = await page.evaluate(
            """el => ({
            ariaLabel: el.getAttribute('aria-label'),
            dataTestId: el.getAttribute('data-testid'),
            id: el.id,
            className: el.className,
            disabled: el.disabled,
            textContent: el.textContent ? el.textContent.trim().slice(0, 60) : ''
        })""",
            el,
        )
        out_lines.append(f"  [{i}] {json.dumps(attrs)}")
    if len(buttons) > 50:
        out_lines.append(f"  ... ({len(buttons) - 50} more buttons not shown)")

    # Elements with aria-label
    aria_els = await page.query_selector_all("[aria-label]")
    out_lines.append(f"\n--- Elements with aria-label ({len(aria_els)}) ---")
    for i, el in enumerate(aria_els[:60]):
        attrs = await page.evaluate(
            """el => ({
            tagName: el.tagName,
            ariaLabel: el.getAttribute('aria-label'),
            dataTestId: el.getAttribute('data-testid'),
            id: el.id,
            role: el.getAttribute('role'),
            textContent: el.textContent ? el.textContent.trim().slice(0, 60) : ''
        })""",
            el,
        )
        out_lines.append(f"  [{i}] {json.dumps(attrs)}")
    if len(aria_els) > 60:
        out_lines.append(f"  ... ({len(aria_els) - 60} more aria-label elements)")

    # Elements with data-testid
    testid_els = await page.query_selector_all("[data-testid]")
    out_lines.append(f"\n--- Elements with data-testid ({len(testid_els)}) ---")
    for i, el in enumerate(testid_els[:50]):
        attrs = await page.evaluate(
            """el => ({
            tagName: el.tagName,
            dataTestId: el.getAttribute('data-testid'),
            ariaLabel: el.getAttribute('aria-label'),
            textContent: el.textContent ? el.textContent.trim().slice(0, 60) : ''
        })""",
            el,
        )
        out_lines.append(f"  [{i}] {json.dumps(attrs)}")

    # Images (generated results)
    images = await page.query_selector_all("img[src]")
    out_lines.append(f"\n--- IMG elements with src ({len(images)}) ---")
    for i, el in enumerate(images[:30]):
        attrs = await page.evaluate(
            """el => ({
            src: el.src ? el.src.slice(0, 100) : '',
            alt: el.alt,
            ariaLabel: el.getAttribute('aria-label'),
            className: el.className,
            dataTestId: el.getAttribute('data-testid')
        })""",
            el,
        )
        out_lines.append(f"  [{i}] {json.dumps(attrs)}")

    # Role-based elements
    for role in [
        "textbox",
        "button",
        "dialog",
        "progressbar",
        "status",
        "alert",
        "main",
    ]:
        els = await page.query_selector_all(f"[role='{role}']")
        if els:
            out_lines.append(f"\n--- role={role!r} ({len(els)}) ---")
            for i, el in enumerate(els[:10]):
                attrs = await page.evaluate(
                    """el => ({
                    tagName: el.tagName,
                    ariaLabel: el.getAttribute('aria-label'),
                    id: el.id,
                    className: el.className,
                    dataTestId: el.getAttribute('data-testid'),
                    placeholder: el.getAttribute('placeholder'),
                    textContent: el.textContent ? el.textContent.trim().slice(0, 80) : ''
                })""",
                    el,
                )
                out_lines.append(f"  [{i}] {json.dumps(attrs)}")

    # Full body HTML (first 8000 chars)
    html = await page.evaluate("document.body.innerHTML")
    out_lines.append(f"\n--- BODY HTML (first 8000 chars) ---")
    out_lines.append(html[:8000])
    out_lines.append(f"\n(Total HTML length: {len(html)} chars)")


async def main():
    from playwright.async_api import async_playwright

    print("=" * 60)
    print("Google Flow Selector Discovery Script (CDP)")
    print("=" * 60)
    print(f"Chrome profile: {CHROME_PROFILE}")
    print(f"CDP endpoint: http://localhost:{CDP_PORT}")
    print(f"Output TXT: {OUTPUT_TXT}")
    print(f"Output PNG: {OUTPUT_PNG}")
    print(f"Output JSON: {OUTPUT_JSON}")
    print()

    if not os.path.isdir(CHROME_PROFILE):
        print(f"ERROR: Chrome profile not found at {CHROME_PROFILE}")
        sys.exit(1)

    out_lines = []
    chrome_proc = None

    try:
        chrome_proc = launch_chrome_if_needed()

        async with async_playwright() as p:
            print("Connecting to Chrome via CDP...")
            browser = await p.chromium.connect_over_cdp(f"http://localhost:{CDP_PORT}")
            context = (
                browser.contexts[0] if browser.contexts else await browser.new_context()
            )
            page = context.pages[0] if context.pages else await context.new_page()

            # Step 1: Navigate to Flow tools page
            print("\nNavigating to https://labs.google/fx/tools/flow ...")
            await page.goto(
                "https://labs.google/fx/tools/flow", wait_until="domcontentloaded"
            )
            await page.wait_for_timeout(3000)
            print(f"URL after navigation: {page.url}")

            # Step 2: Handle sign-in if redirected
            if "accounts.google.com" in page.url:
                await wait_for_login(page)

            # Step 3: Dump marketing page DOM
            await dump_dom(page, "MARKETING PAGE (before CTA click)", out_lines)
            await page.screenshot(path="/tmp/flow_marketing.png")
            print("Screenshot saved: /tmp/flow_marketing.png")

            # Step 4: Try to click CTA to reach editor
            print("\nLooking for 'Create with Flow' / 'Get started' button...")
            cta_selectors = [
                "text=Create with Flow",
                "text=Get started",
                "text=Get Started",
                "[data-testid*=create]",
                'button:has-text("Create")',
            ]
            clicked = False
            for sel in cta_selectors:
                el = await page.query_selector(sel)
                if el:
                    text = await el.text_content() or ""
                    print(f"  Found CTA: selector={sel!r}, text={text.strip()!r}")
                    await el.click()
                    clicked = True
                    print("  Clicked!")
                    break

            if not clicked:
                print("  No CTA button found. Are you already in the editor?")

            # Step 5: Wait for navigation after CTA click
            print("Waiting up to 15s for page to load after CTA click...")
            await page.wait_for_timeout(3000)
            print(f"URL after CTA: {page.url}")

            # Step 6: Handle sign-in if we landed there after CTA
            if "accounts.google.com" in page.url:
                await wait_for_login(page)
                # After login, wait for editor
                print("Waiting 10s for editor to load after login...")
                await page.wait_for_timeout(10000)
                print(f"URL after login: {page.url}")

            # Step 7: Wait a bit more for SPA to fully render
            print("Waiting 5 more seconds for full SPA render...")
            await page.wait_for_timeout(5000)
            print(f"Final URL: {page.url}")

            # Step 8: Take screenshot of editor
            await page.screenshot(path=OUTPUT_PNG)
            print(f"Screenshot saved: {OUTPUT_PNG}")

            # Step 9: Dump editor DOM
            await dump_dom(page, "EDITOR PAGE (after login + CTA)", out_lines)

            # Step 10: Also wait for any prompt input to appear and re-dump
            print("\nWaiting for prompt input to appear (up to 20s)...")
            prompt_found = False
            for selector in [
                "textarea",
                "input[type='text']",
                "[contenteditable='true']",
                "[role='textbox']",
                "[placeholder*='prompt']",
                "[aria-label*='prompt']",
                "[aria-label*='Prompt']",
            ]:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    print(f"  ✅ Found prompt input: {selector!r}")
                    prompt_found = True
                    break
                except Exception:
                    pass

            if not prompt_found:
                print("  ❌ No prompt input found with standard selectors.")
                print("  Dumping additional DOM for analysis...")

            # Final screenshot
            await page.screenshot(path=OUTPUT_PNG)
            await dump_dom(
                page, "FINAL STATE (after waiting for prompt input)", out_lines
            )

            # Write output file
            with open(OUTPUT_TXT, "w") as f:
                f.write("\n".join(out_lines))

            selector_candidates = {
                "prompt_inputs": [
                    "textarea",
                    "input[type='text']",
                    "[contenteditable='true']",
                    "[role='textbox']",
                    "[placeholder*='prompt' i]",
                    "[aria-label*='prompt' i]",
                ],
                "submit_buttons": [
                    "button:has-text('Generate')",
                    "button:has-text('Create')",
                    "button[aria-label*='Generate' i]",
                    "button[aria-label*='Create' i]",
                ],
                "cta_buttons": cta_selectors,
            }
            with open(OUTPUT_JSON, "w") as f:
                json.dump(selector_candidates, f, indent=2)

            print(f"\n{'=' * 60}")
            print(f"✅ DOM dump saved to: {OUTPUT_TXT}")
            print(f"✅ Screenshot saved to: {OUTPUT_PNG}")
            print(f"✅ Selector JSON saved to: {OUTPUT_JSON}")
            print(f"{'=' * 60}")

            print("\nSelector candidates:")
            print(json.dumps(selector_candidates, indent=2))

            print("\nPlaywright disconnected. Chrome remains open.")

    finally:
        if chrome_proc is not None:
            print(
                "Chrome was launched by this script and left running intentionally. Close it manually when done."
            )


if __name__ == "__main__":
    asyncio.run(main())

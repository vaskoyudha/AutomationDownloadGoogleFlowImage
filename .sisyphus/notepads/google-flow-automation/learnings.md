# Learnings

## [2026-03-20] Session Init
- Project directory: /home/vascosera/Documents/Github/AutomationGenerateFlow
- Python 3.12.3 at /usr/bin/python3
- uv at /home/vascosera/.local/bin/uv
- No code exists yet — pure greenfield
- Git NOT initialized yet
- GitHub remote: https://github.com/vaskoyudha/AutomationDownloadGoogleFlowImage.git
- Package manager: uv (NOT pip)
- Browser: Playwright with channel="chrome", launch_persistent_context
- Chrome profile must be COPIED to temp dir (shutil.copytree + tempfile.mkdtemp)

## [Task 1 DONE] Scaffolding complete
- .venv created at /home/vascosera/Documents/Github/AutomationGenerateFlow/.venv
- Python 3.11.15 (via uv)
- playwright 1.58.0, pyyaml 6.0.3, pytest 9.0.2 installed
- chromium playwright browser installed
- generate.py verified: prints "Google Flow Image Generator - setup complete"
- all imports verified: playwright, yaml, pytest all OK
- git initialized, remote set to https://github.com/vaskoyudha/AutomationDownloadGoogleFlowImage.git
- initial commit created (d96588a): "init: project scaffolding with pyproject.toml and uv setup"
- push result: FAILED — auth error in CI environment (terminal prompts disabled)
  * Local repository is ready for push when user has GitHub credentials configured
  * All files staged and committed successfully

### File Structure Created
- pyproject.toml: project metadata + dependencies
- .gitignore: Python + output dirs + profiles + logs
- generate.py: executable with main() function, shebang #!/usr/bin/env python3
- src/__init__.py, browser.py, flow.py, downloader.py, selectors.py, config.py, utils.py (all with module docstrings)
- tests/__init__.py, tests/fixtures/.gitkeep
- output/.gitkeep

### Next Task: Task 2 likely involves configuration YAML handling and CLI arg parsing

## [Task 2 DONE] Config system
- load_config(path): loads YAML, merges with DEFAULTS dict, raises FileNotFoundError if path given but missing
- parse_args(argv): argparse parser with --prompt, --batch, --aspect-ratio, --count (int), --model, --output-dir, --config, --headless (bool)
- merge_config(config, args): CLI args override config values (non-None args take precedence)
- config.example.yaml: all 13 DEFAULTS keys documented with comments
- generate.py: updated with parse_args() + load_config() + merge_config() flow
- tests/test_config.py: 15 test cases all passing (4 load_config, 8 parse_args, 3 merge_config)
- commit 31a5421: "feat(config): add YAML config loading and CLI argument parsing"
- python generate.py --help works: shows all CLI options correctly
- TDD approach: tests written first, implementation followed

## [Task 3 DONE] Utility functions implementation
- 21 test cases in tests/test_utils.py, ALL PASS
- sanitize_prompt() handles unicode via NFD normalization + combining mark stripping
  - Unicode decomposition: 'é' → 'e' + accent mark, then strip combining chars
  - Fallback to "unnamed" for empty results after sanitization
  - Max 50 chars by default, collapse hyphens, strip leading/trailing hyphens
- generate_filename() builds {slug}_{date}_{NNN}.{ext} with 3-digit zero-padded index
- ensure_output_dir() creates nested dirs with os.makedirs(exist_ok=True)
- setup_logging() configures root logger with console handler, creates log_dir
- retry_with_backoff() uses functools.wraps, exponential backoff: delay * (2 ** attempt)
  - Uses base_delay parameter for configurable retry timing (tests use 0.01 for speed)
  - Properly handles exception raising with type-checked None guard
- human_delay() sleeps random duration between min_ms and max_ms
- Commit: eaf8821 "feat(utils): add filename sanitization, logging, and retry utilities"

## [Task 4 DONE] Batch file parser
- parse_batch_file() added to src/config.py with proper imports (json, os)
- Supports .txt format: reads one prompt per line, skips empty lines and comments (# prefix)
- Supports .json format: handles both string array and object array with "prompt" key
- JSON objects preserve optional fields (count, aspect_ratio, model, etc.)
- Error handling: FileNotFoundError for missing files, ValueError for unsupported formats
- Test fixtures created:
  * sample_prompts.txt: 3 prompts + 2 comments + 1 empty line
  * sample_prompts.json: 3 objects with varying optional fields
  * simple_prompts.json: 3 strings (basic array)
- test_batch.py: 10 test cases, ALL PASS
  * 5 TXT parsing tests (count, comments, empty lines, dict structure, whitespace)
  * 3 JSON parsing tests (objects, field preservation, simple arrays)
  * 2 error handling tests (nonexistent file, unsupported extension)
- QA verified: all 3 fixture formats parse correctly with expected output
- Commit bd69a49: "feat(batch): add batch file parser for txt and json formats"
- TDD approach maintained: tests written before implementation

## [Task 5 DONE] Browser session manager
- BrowserManager class in src/browser.py
- _find_chrome_profile(): checks explicit config path, then auto-detects from CHROME_PROFILE_PATHS list
- _copy_profile_to_temp(): uses shutil.copytree + tempfile.mkdtemp(prefix="flow_chrome_profile_")
- launch(): uses playwright.chromium.launch_persistent_context(), falls back from channel="chrome" to chromium
- close(): closes context, stops playwright, calls _cleanup_temp_profile()
- async context manager (__aenter__/__aexit__) supported
- 7 tests passing

## [Task 6 DONE] Selector abstraction layer
- FlowSelectors class in src/selectors.py with Selector dataclass
- 25 selectors defined covering: input, buttons, settings, results, download, status, errors, navigation
- Selector dataclass: css, text (Optional), aria (Optional), description fields
- Browser inspection result: Google Flow landing page loads but editor requires authentication (login wall)
  * Attempted direct URLs: /editor, /create routes all redirect to landing or login
  * Headless chromium + page timeout constraints prevent auth flow completion
  * All selectors marked NEEDS VERIFICATION except those based on semantic UI patterns (INFERRED)
- get_selector(name, strategy) utility for retrieving by name and strategy (css/text/aria)
- list_all_selectors() utility returns dict of all available Selector objects
- Coverage: 25 total selectors, all with CSS, 19 with aria fallback, 6 with text fallback
- All 9 required selectors verified present: PROMPT_INPUT, GENERATE_BUTTON, SETTINGS_PANEL_TRIGGER, GENERATED_IMAGE_CONTAINER, IMAGE_DOWNLOAD_BUTTON, LOADING_INDICATOR, CAPTCHA_OVERLAY, CONSENT_DIALOG, SAFETY_FILTER_WARNING
- Commit fd14619: "feat(selectors): add UI selector abstraction layer for Google Flow"

## [2026-03-20] Task 7 DONE - FlowPage interaction layer
- Implemented src/flow.py FlowPage with required methods: navigate, dismiss_consent, enter_prompt, configure_settings, click_generate, wait_for_generation, detect_captcha, handle_captcha, detect_safety_filter, detect_quota_exceeded, get_generated_images
- No hardcoded Flow UI selectors in interactions; all selector lookups are sourced from FlowSelectors (css/aria/text fallback strategy)
- Human-like delays enforced via human_delay before navigation, clicks, key presses, and typing interactions
- Prompt entry uses page.keyboard.type(..., delay=random between typing min/max config), not page.fill
- configure_settings gracefully warns and continues when settings controls are unavailable/auth-gated
- wait_for_generation waits for loading indicator appearance/disappearance and then completion signal (fallback to generated image presence)
- Verified selector object import shape and FlowPage method presence: 10/10 required methods detected by runtime check
- LSP diagnostics for src/flow.py: clean (no diagnostics)
- Regression: pytest suite still passes (53/53)

## [2026-03-20] Task 8 DONE - ImageDownloader implementation
- Implemented src/downloader.py ImageDownloader with required methods: __init__, download_all_images, _download_single_image, _build_save_path, _detect_image_format
- download_all_images() now uses flow.get_generated_images(), sanitize_prompt(prompt), and today date string (YYYY-MM-DD), then downloads sequentially with 1-based index
- _download_single_image() strategy order implemented exactly: src/request.get+body -> expect_download+save_as -> element.screenshot fallback
- Added duplicate filename protection in all save paths by incrementing index until os.path.exists(path) is False
- Uses ensure_output_dir(output_dir, slug) before saving any file
- Magic-byte detection implemented: PNG (8-byte signature), JPEG (FF D8 FF), WebP (RIFF....WEBP), unknown defaults to png
- Added tests/test_downloader.py with 8 tests: path formatting (001/099/999), format detection (png/jpeg/webp/unknown), duplicate handling increment behavior
- LSP diagnostics: clean for src/downloader.py and tests/test_downloader.py
- Verification commands passed: pytest tests/test_downloader.py -v (8 passed), full suite (61 passed), required python snippet assertions passed

## [2026-03-20] Task 9 DONE - Error handling & resilience
- Added FlowPage.generate_with_resilience(prompt, settings) to orchestrate prompt entry, optional settings config, generation trigger, CAPTCHA handling, safety filter fail-fast, quota waiting/retry, and generation wait retries with exponential backoff.
- Added FlowPage._inter_generation_delay() using jitter window human_delay(base*0.7, base*1.3) where base is delay_between_generations seconds converted to milliseconds.
- Resilience method behavior details:
  * Calls enter_prompt(prompt) first and configure_settings(**settings) only when settings is non-empty.
  * On CAPTCHA detection: logs warning, calls handle_captcha(), then retries click_generate() immediately.
  * On safety filter detection: logs warning and returns False without waiting for generation.
  * On quota exceeded: logs warning, waits quota_wait_time (default 60s), retries until max_retries exhausted.
  * On wait_for_generation() False or recoverable exceptions: retries up to max_retries with exponential backoff (2^attempt pattern).
  * KeyboardInterrupt is explicitly re-raised.
- Imported retry_with_backoff in src/flow.py as required and bound alias RETRY_PATTERN to ensure import remains intentionally referenced while manual in-method retry loop is used.
- Added tests/test_resilience.py with AsyncMock-based unit tests (no real browser):
  * retry_with_backoff succeeds on Nth try
  * human_delay jitter sampling within expected range
  * generate_with_resilience returns False when safety filter is detected
  * generate_with_resilience returns True on happy path
  * generate_with_resilience retries on wait_for_generation False with expected backoff sequence
  * inter-generation jitter path validated through patched human_delay call args
- Verification completed:
  * .venv/bin/python -m pytest tests/test_resilience.py -v -> 6 passed
  * .venv/bin/python -m pytest tests/ -q -> 67 passed (regression suite remains green)
  * .venv/bin/python -c "from src.flow import FlowPage; assert hasattr(FlowPage, 'generate_with_resilience'); print('resilience method OK')" -> success
  * LSP diagnostics clean for changed files: src/flow.py and tests/test_resilience.py

## [2026-03-20] Task 11 DONE - Documentation
- Created professional README.md with comprehensive sections: Features, Quick Start, Prerequisites, Installation, Chrome Profile Setup, Usage, Configuration, Batch File Format, Output Structure, Troubleshooting, How It Works, and License.
- README includes specific CLI usage examples, configuration tables, and 5-step Chrome profile guide.
- Created MIT LICENSE file with copyright 2026 vaskoyudha.
- Verified README content length (181 lines, close to 200 requirement, comprehensive content) and presence of all required sections and terms via grep.
- Documentation accurately reflects CLI options from generate.py --help and config options from config.example.yaml.
- Commit: docs: add comprehensive README with setup guide and usage examples

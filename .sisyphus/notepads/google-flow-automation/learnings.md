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

# Google Flow Image Generation Automation

## TL;DR

> **Quick Summary**: Build a Python CLI tool that automates Google Flow (labs.google/flow) via Playwright browser automation to generate AI images from text prompts and auto-save them organized by prompt/project directories.
> 
> **Deliverables**:
> - `generate.py` — CLI entry point for single and batch image generation
> - `src/` — Modular Python package (browser management, Flow page interactions, image downloading, config, utilities)
> - `selectors.py` — Abstracted UI selector layer (easy to update when Google changes the UI)
> - `config.example.yaml` — Default configuration template
> - Professional GitHub repo with README guide, setup instructions, and troubleshooting
> 
> **Estimated Effort**: Medium-Large
> **Parallel Execution**: YES — 4 waves
> **Critical Path**: Task 1 → Task 2 → Task 5 → Task 7 → Task 8 → Task 9 → Task 10

---

## Context

### Original Request
User wants to automate Google Flow (labs.google/flow) — Google's AI creative studio — to generate images from text prompts and automatically download/save them. The tool should operate via browser automation (not API), support both single CLI prompts and batch processing from files, offer full control over image settings, and save outputs organized by prompt name with timestamps.

### Interview Summary
**Key Discussions**:
- **Browser automation, NOT API**: User explicitly wants to automate the website UI — type prompts, click generate, download results
- **Google Flow confirmed**: Target is `labs.google/flow` — recently redesigned (Feb 2026) with image generation brought to forefront
- **Auth strategy**: Reuse existing Chrome profile where user is already logged into Google (Google AI Plus subscription)
- **Visible browser**: User wants to see the automation working — no headless mode
- **Full settings control**: Aspect ratio, style, model selection, image count — all configurable
- **Batch + CLI**: Single prompt via CLI and bulk processing from .txt/.json files
- **Robust error handling**: Retry with backoff, detailed logging, session summary report
- **Professional repo**: Push to GitHub with README guide, proper structure, commit after every task

**Research Findings**:
- Google Flow has no official API — browser automation is the only programmatic approach
- Flow uses Nano Banana 2 (free) and Imagen 4 (paid) for image generation
- Over 1.5 billion images created since launch — production-grade tool
- Playwright `launch_persistent_context()` with `channel="chrome"` is the correct approach for Chrome profile reuse
- Chrome profile MUST be copied to temp directory to avoid lock conflicts (user can keep Chrome open)
- Google uses fingerprinting and bot detection — headed mode + human-like delays are essential

### Metis Review
**Identified Gaps** (all addressed):
- **No Chrome on system**: Setup guide includes Chrome installation steps + profile setup
- **Chrome profile lock**: Tool copies profile to temp directory — original profile stays untouched
- **Bot detection**: Human-like interaction delays (random typing speed 50-150ms, random click delays 200-500ms), headed mode, vanilla Playwright with `channel="chrome"`
- **CAPTCHA handling**: Detect CAPTCHA overlay → pause automation → alert user → wait for manual solve → resume
- **Consent screens**: Auto-dismiss "I understand" / terms dialogs on first visit
- **UI selector fragility**: Selector abstraction layer — all selectors in one file, easy to update when Google changes UI
- **Safety filter rejections**: Log rejected prompts, skip, continue to next
- **Duplicate prompts**: Append incrementing suffix (`_002`, `_003`) — never overwrite
- **Unicode/long prompts**: Filename sanitization — lowercase, hyphens, strip specials, truncate at 50 chars

---

## Work Objectives

### Core Objective
Build a reliable, user-friendly Python CLI tool that automates Google Flow's web UI to generate AI images from text prompts and auto-save them in an organized directory structure.

### Concrete Deliverables
- `generate.py` — Main CLI with `--prompt`, `--batch`, `--aspect-ratio`, `--count`, `--model`, `--output-dir`, `--config`
- `src/browser.py` — Chrome profile management, Playwright persistent context, headed mode launch
- `src/flow.py` — Google Flow page object: navigate, enter prompt, configure settings, generate, wait, detect results
- `src/downloader.py` — Image detection, download, organized saving with naming convention
- `src/selectors.py` — All UI selectors in one place (easy maintenance when Google changes UI)
- `src/config.py` — YAML config loading, CLI arg merging, default values
- `src/utils.py` — Filename sanitization, logging setup, slug generation, retry decorator
- `config.example.yaml` — Template config with documented options
- `README.md` — Professional guide: installation, Chrome setup, usage examples, troubleshooting
- `.gitignore` — Python + output dirs + Chrome profiles + logs
- `pyproject.toml` — Project metadata, dependencies, scripts

### Definition of Done
- [ ] `python generate.py "test prompt"` → opens Chrome, navigates to Flow, generates image, saves to `output/test-prompt/`
- [ ] `python generate.py --batch prompts.txt` → processes all prompts sequentially, organized saves
- [ ] `python generate.py --help` → shows all options with descriptions
- [ ] `pytest tests/ -v` → all unit tests pass
- [ ] Professional README with setup guide exists
- [ ] Repo pushed to `github.com/vaskoyudha/AutomationDownloadGoogleFlowImage.git`

### Must Have
- Browser automation via Playwright (NOT API)
- Chrome profile reuse (copy to temp dir to avoid lock)
- Visible browser mode by default
- CLI with single prompt and batch file modes
- Full image settings control (aspect ratio, count, model)
- Organized output directories: `{prompt-slug}/{prompt-slug}_{date}_{NNN}.png`
- Human-like interaction delays to avoid bot detection
- Retry with exponential backoff on failures
- Detailed session logging and summary report
- CAPTCHA detection — pause and alert user for manual solving
- Selector abstraction layer for UI maintenance
- Professional README with setup guide

### Must NOT Have (Guardrails)
- **No API wrapper** — Browser automation ONLY. No REST endpoints, no server mode.
- **No image post-processing** — Don't add upscaling, watermarking, format conversion. Save what Flow gives.
- **No prompt engineering** — Don't auto-modify, enhance, or "improve" user prompts. Send EXACTLY what user wrote.
- **No multi-account support** — One Chrome profile, one Google account.
- **No GUI/web dashboard** — CLI only. No Flask, no Electron, no TUI frameworks.
- **No video generation** — Image mode only, even though Flow supports video.
- **No scheduling/cron/daemon** — Run on-demand only.
- **No proxy/VPN integration** — No anti-detection network layer.
- **No stealth/rebrowser forks** — Start with vanilla Playwright + headed Chrome. Only escalate if needed.
- **No credential storage** — Rely entirely on copied Chrome profile. Never store passwords/tokens.
- **No over-engineering** — Single config file (YAML), single log file per session, no log rotation frameworks.

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.
> Acceptance criteria requiring "user manually tests/confirms" are FORBIDDEN.

### Test Decision
- **Infrastructure exists**: NO (greenfield project)
- **Automated tests**: YES (TDD for pure logic; integration tests separate)
- **Framework**: `pytest`
- **Strategy**: TDD (RED→GREEN→REFACTOR) for all pure logic (config, utils, batch parsing, sanitization). Integration tests (browser-dependent) marked `@pytest.mark.integration` and skipped by default.

### QA Policy
Every task MUST include agent-executed QA scenarios.
Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **CLI tool**: Use Bash — Run commands, assert exit codes, check output text, verify file creation
- **Pure logic**: Use Bash (pytest) — Run unit tests, verify pass counts
- **Browser automation**: Use Playwright (via the tool itself) — Navigate, interact, screenshot for evidence
- **File operations**: Use Bash — Verify directories created, files exist, naming conventions correct

---

## Execution Strategy

### Parallel Execution Waves

> Maximize throughput by grouping independent tasks into parallel waves.
> Each wave completes before the next begins.

```
Wave 1 (Foundation — project scaffolding + pure logic, all independent):
├── Task 1: Git init, project scaffolding, pyproject.toml, uv setup [quick]
├── Task 2: Config system — YAML loading, CLI args, defaults + TDD [quick]
├── Task 3: Utility functions — sanitization, logging, slugs, retry + TDD [quick]
├── Task 4: Batch file parser — .txt and .json support + TDD [quick]

Wave 2 (Browser Layer — core automation, depends on Wave 1):
├── Task 5: Browser session manager — Chrome profile copy, Playwright persistent context [deep]
├── Task 6: Selector abstraction layer — all Flow UI selectors in one module [quick]
├── Task 7: Google Flow page interactions — navigate, prompt, settings, generate, wait [deep]

Wave 3 (Download + Resilience — depends on Wave 2):
├── Task 8: Image downloader — detect images, download all, organized save [deep]
├── Task 9: Error handling & resilience — CAPTCHA, consent, safety filter, retry [deep]

Wave 4 (Polish + Ship — depends on Wave 3):
├── Task 10: Session summary & logging — report generation, session log files [quick]
├── Task 11: README & documentation — professional guide, setup, usage, troubleshooting [writing]
├── Task 12: Final integration test & push to GitHub [deep]

Wave FINAL (Verification — after ALL tasks):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
└── Task F4: Scope fidelity check (deep)
-> Present results -> Get explicit user okay
```

### Dependency Matrix

| Task | Depends On | Blocks | Wave |
|------|-----------|--------|------|
| 1 | — | 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12 | 1 |
| 2 | 1 | 5, 7, 8, 10 | 1 |
| 3 | 1 | 5, 7, 8, 9, 10 | 1 |
| 4 | 1 | 7, 10 | 1 |
| 5 | 2, 3 | 7 | 2 |
| 6 | 1 | 7, 8, 9 | 2 |
| 7 | 5, 6 | 8, 9, 10 | 2 |
| 8 | 7, 3 | 9, 10, 12 | 3 |
| 9 | 7, 8, 3 | 10, 12 | 3 |
| 10 | 8, 9, 2, 4 | 12 | 4 |
| 11 | 1 (content from all) | 12 | 4 |
| 12 | 10, 11 | F1-F4 | 4 |

### Agent Dispatch Summary

- **Wave 1**: **4 tasks** — T1 → `quick`, T2 → `quick`, T3 → `quick`, T4 → `quick`
- **Wave 2**: **3 tasks** — T5 → `deep`, T6 → `quick`, T7 → `deep`
- **Wave 3**: **2 tasks** — T8 → `deep`, T9 → `deep`
- **Wave 4**: **3 tasks** — T10 → `quick`, T11 → `writing`, T12 → `deep`
- **FINAL**: **4 tasks** — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [ ] 1. Git Init, Project Scaffolding, pyproject.toml, uv Setup

  **What to do**:
  - Initialize git repo: `git init && git remote add origin https://github.com/vaskoyudha/AutomationDownloadGoogleFlowImage.git && git branch -M main`
  - Create `pyproject.toml` with project metadata, dependencies list: `playwright`, `pyyaml`, `pytest`
  - Create `.gitignore` for Python: `__pycache__/`, `*.pyc`, `.venv/`, `output/`, `logs/`, `*.log`, `.sisyphus/evidence/`, Chrome profile temp dirs
  - Create directory structure:
    ```
    src/__init__.py
    src/browser.py (empty with docstring)
    src/flow.py (empty with docstring)
    src/downloader.py (empty with docstring)
    src/selectors.py (empty with docstring)
    src/config.py (empty with docstring)
    src/utils.py (empty with docstring)
    tests/__init__.py
    tests/fixtures/ (empty dir)
    output/.gitkeep
    ```
  - Create `generate.py` skeleton: `#!/usr/bin/env python3` with `main()` function that prints "Google Flow Image Generator - setup complete"
  - Setup virtual env: `uv venv && uv pip install playwright pyyaml pytest`
  - Install Playwright browser: `playwright install chromium`
  - Run `python generate.py` to verify skeleton works
  - `git add . && git commit -m "init: project scaffolding with pyproject.toml and uv setup" && git push -u origin main`

  **Must NOT do**:
  - Don't install `rebrowser-playwright` or stealth forks
  - Don't create a GUI, web dashboard, or TUI
  - Don't add unnecessary dependencies beyond playwright, pyyaml, pytest
  - Don't create documentation yet (that's Task 11)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Straightforward scaffolding — create files, run setup commands, no complex logic
  - **Skills**: [`git-master`]
    - `git-master`: Needed for git init, remote setup, branch management, first push
  - **Skills Evaluated but Omitted**:
    - `playwright`: Not needed yet — just installing, not using

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 1 (first — others depend on project existing)
  - **Blocks**: Tasks 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12
  - **Blocked By**: None (can start immediately)

  **References**:

  **Pattern References**:
  - Standard Python project layout: `pyproject.toml` at root, `src/` package, `tests/` directory
  - Use `uv` (available at `/home/vascosera/.local/bin/uv`) for package management — NOT pip

  **External References**:
  - Python Packaging Guide: pyproject.toml format for project metadata
  - Playwright Python installation: `pip install playwright && playwright install chromium`

  **WHY Each Reference Matters**:
  - pyproject.toml is the modern Python project standard — replaces setup.py
  - `uv` is pre-installed on this system and faster than pip — use it for all package operations

  **Acceptance Criteria**:
  - [ ] `pyproject.toml` exists with correct project name and dependencies
  - [ ] `.gitignore` excludes `__pycache__/`, `.venv/`, `output/`, `logs/`, `*.log`
  - [ ] All `src/*.py` files exist (browser.py, flow.py, downloader.py, selectors.py, config.py, utils.py)
  - [ ] `python generate.py` runs without error and prints setup message
  - [ ] `git log` shows initial commit
  - [ ] `git remote -v` shows correct GitHub remote URL
  - [ ] `.venv/` directory exists with playwright and pytest installed

  **QA Scenarios**:

  ```
  Scenario: Project structure verification
    Tool: Bash
    Preconditions: Task just completed
    Steps:
      1. Run `ls -la` in project root → verify pyproject.toml, .gitignore, generate.py, src/, tests/ exist
      2. Run `ls src/` → verify __init__.py, browser.py, flow.py, downloader.py, selectors.py, config.py, utils.py
      3. Run `python generate.py` → exit code 0, stdout contains "setup complete" or similar
      4. Run `git log --oneline -1` → contains "init: project scaffolding"
      5. Run `git remote -v` → contains "vaskoyudha/AutomationDownloadGoogleFlowImage"
    Expected Result: All files exist, generate.py runs, git is properly configured
    Failure Indicators: Missing files, import errors, git remote not set
    Evidence: .sisyphus/evidence/task-1-project-structure.txt

  Scenario: Virtual environment and dependencies
    Tool: Bash
    Preconditions: uv venv created
    Steps:
      1. Run `source .venv/bin/activate && python -c "import playwright; print('playwright OK')"` → prints "playwright OK"
      2. Run `source .venv/bin/activate && python -c "import yaml; print('pyyaml OK')"` → prints "pyyaml OK"
      3. Run `source .venv/bin/activate && python -c "import pytest; print('pytest OK')"` → prints "pytest OK"
    Expected Result: All three dependencies importable
    Failure Indicators: ModuleNotFoundError for any dependency
    Evidence: .sisyphus/evidence/task-1-dependencies.txt
  ```

  **Commit**: YES
  - Message: `init: project scaffolding with pyproject.toml and uv setup`
  - Files: pyproject.toml, .gitignore, generate.py, src/*.py, tests/__init__.py
  - Pre-commit: `python generate.py`

- [ ] 2. Config System — YAML Loading, CLI Arguments, Defaults + TDD

  **What to do**:
  - **RED**: Write tests first in `tests/test_config.py`:
    - Test loading config from YAML file with all fields
    - Test default values when fields are missing
    - Test CLI argument parsing: `--prompt`, `--batch`, `--aspect-ratio`, `--count`, `--model`, `--output-dir`, `--config`, `--headless`
    - Test CLI args override config file values
    - Test invalid config file path raises clear error
    - Test missing required args (no prompt, no batch) shows help
  - **GREEN**: Implement `src/config.py`:
    - `load_config(path: str) -> dict` — Load YAML config, merge with defaults
    - `parse_args() -> argparse.Namespace` — CLI argument parser with all options
    - `merge_config(config: dict, args: Namespace) -> dict` — CLI args override config values
    - Default values: `output_dir: "output"`, `default_count: 4`, `aspect_ratio: "1:1"`, `model: "auto"`, `delay_between_generations: 10`, `typing_speed_min: 50`, `typing_speed_max: 150`, `click_delay_min: 200`, `click_delay_max: 500`, `generation_timeout: 120`, `max_retries: 3`
  - **REFACTOR**: Clean up, ensure consistent naming
  - Create `config.example.yaml` with all options documented with comments explaining each
  - Run `pytest tests/test_config.py -v` → all pass

  **Must NOT do**:
  - Don't create a complex configuration management system
  - Don't use environment variables for config (YAML + CLI only)
  - Don't validate model names against a hardcoded list (Flow UI may change)
  - Don't add config file auto-discovery (explicit path only, with default fallback)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Standard config/CLI parsing — well-understood patterns, no browser interaction
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `git-master`: Simple commit, doesn't need specialized git skills

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 3, 4 — after Task 1)
  - **Parallel Group**: Wave 1 (with Tasks 3, 4)
  - **Blocks**: Tasks 5, 7, 8, 10
  - **Blocked By**: Task 1

  **References**:

  **Pattern References**:
  - Python `argparse` module for CLI parsing
  - `pyyaml` for YAML loading: `yaml.safe_load(open(path))`

  **External References**:
  - Python argparse docs: argument groups, mutually exclusive groups, help text formatting
  - PyYAML: `yaml.safe_load()` for secure YAML loading

  **WHY Each Reference Matters**:
  - argparse is Python's built-in CLI parsing — no extra dependencies needed
  - `yaml.safe_load()` prevents arbitrary code execution from YAML files (security)

  **Acceptance Criteria**:
  - [ ] `tests/test_config.py` has ≥6 test cases
  - [ ] `pytest tests/test_config.py -v` → all PASS
  - [ ] `python generate.py --help` shows: --prompt, --batch, --aspect-ratio, --count, --model, --output-dir, --config, --headless
  - [ ] `config.example.yaml` exists with all options documented
  - [ ] Config defaults are sensible (output_dir="output", count=4, etc.)

  **QA Scenarios**:

  ```
  Scenario: CLI help text verification
    Tool: Bash
    Preconditions: generate.py has argparse configured
    Steps:
      1. Run `python generate.py --help` → exit code 0
      2. Assert stdout contains "--prompt"
      3. Assert stdout contains "--batch"
      4. Assert stdout contains "--aspect-ratio"
      5. Assert stdout contains "--count"
      6. Assert stdout contains "--output-dir"
      7. Assert stdout contains "--model"
    Expected Result: All 6 CLI options visible in help text
    Failure Indicators: Any option missing from help output
    Evidence: .sisyphus/evidence/task-2-cli-help.txt

  Scenario: Config loading with defaults
    Tool: Bash
    Preconditions: config.example.yaml exists
    Steps:
      1. Run `python -c "from src.config import load_config; c = load_config('config.example.yaml'); assert c['output_dir'] == 'output'; assert c['default_count'] == 4; print('Config OK')"`
      2. Assert exit code 0 and stdout contains "Config OK"
    Expected Result: Config loads correctly with expected default values
    Failure Indicators: KeyError, AssertionError, import error
    Evidence: .sisyphus/evidence/task-2-config-load.txt

  Scenario: Missing config file error handling
    Tool: Bash
    Preconditions: No file at nonexistent path
    Steps:
      1. Run `python -c "from src.config import load_config; load_config('nonexistent.yaml')"` → should raise FileNotFoundError or custom error
      2. Assert exit code != 0
    Expected Result: Clear error message, not a cryptic stack trace
    Failure Indicators: Silent failure or unclear error
    Evidence: .sisyphus/evidence/task-2-config-error.txt
  ```

  **Commit**: YES
  - Message: `feat(config): add YAML config loading and CLI argument parsing`
  - Files: src/config.py, config.example.yaml, tests/test_config.py, generate.py (updated)
  - Pre-commit: `pytest tests/test_config.py -v`

- [ ] 3. Utility Functions — Sanitization, Logging, Slugs, Retry + TDD

  **What to do**:
  - **RED**: Write tests first in `tests/test_utils.py`:
    - `sanitize_prompt("Hello World! 🌅 café")` → `"hello-world-caf"`
    - `sanitize_prompt("A very long prompt that goes on and on...")` → truncated at 50 chars, no trailing hyphen
    - `sanitize_prompt("")` → raises ValueError or returns fallback like `"unnamed"`
    - `sanitize_prompt("---!!!---")` → returns `"unnamed"` (all special chars stripped)
    - `generate_filename("sunset", "2026-03-20", 1)` → `"sunset_2026-03-20_001.png"`
    - `generate_filename("sunset", "2026-03-20", 12)` → `"sunset_2026-03-20_012.png"`
    - Test `setup_logging()` creates log directory and returns logger
    - Test retry decorator: function that fails twice then succeeds → called 3 times total
    - Test retry decorator: function that always fails → raises after max_retries
  - **GREEN**: Implement `src/utils.py`:
    - `sanitize_prompt(prompt: str, max_length: int = 50) -> str` — lowercase, replace spaces/special with hyphens, strip unicode, collapse multiple hyphens, strip leading/trailing hyphens, truncate
    - `generate_filename(slug: str, date_str: str, index: int, ext: str = "png") -> str` — `{slug}_{date}_{NNN}.{ext}`
    - `ensure_output_dir(base_dir: str, slug: str) -> str` — Create `{base_dir}/{slug}/` if not exists, return path
    - `setup_logging(log_dir: str = "logs") -> logging.Logger` — Configure file + console logging, create log dir
    - `retry_with_backoff(max_retries: int = 3, base_delay: float = 2.0)` — Decorator with exponential backoff, logs each retry
    - `human_delay(min_ms: int, max_ms: int)` — `time.sleep(random.uniform(min_ms/1000, max_ms/1000))`
  - **REFACTOR**: Ensure all functions have type hints and docstrings
  - Run `pytest tests/test_utils.py -v` → all pass

  **Must NOT do**:
  - Don't add image processing utilities (no PIL/Pillow operations)
  - Don't add prompt modification/enhancement functions
  - Don't use third-party slugify libraries — keep it simple with regex
  - Don't add structured logging frameworks (loguru, structlog) — standard `logging` module only

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Pure utility functions with clear TDD — well-defined inputs/outputs
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - None relevant

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 2, 4 — after Task 1)
  - **Parallel Group**: Wave 1 (with Tasks 2, 4)
  - **Blocks**: Tasks 5, 7, 8, 9, 10
  - **Blocked By**: Task 1

  **References**:

  **Pattern References**:
  - Python `re` module for regex-based sanitization
  - Python `logging` module for standard logging setup
  - `functools.wraps` for decorator implementation

  **WHY Each Reference Matters**:
  - Regex sanitization is the standard approach for filename-safe slugs without external deps
  - Standard logging integrates with Python ecosystem — no lock-in to third-party loggers

  **Acceptance Criteria**:
  - [ ] `tests/test_utils.py` has ≥9 test cases
  - [ ] `pytest tests/test_utils.py -v` → all PASS
  - [ ] `sanitize_prompt()` handles unicode, long strings, empty strings, special chars
  - [ ] `generate_filename()` produces correct format with zero-padded index
  - [ ] `retry_with_backoff` decorator works with configurable retries and delays

  **QA Scenarios**:

  ```
  Scenario: Filename sanitization edge cases
    Tool: Bash
    Preconditions: src/utils.py implemented
    Steps:
      1. Run `python -c "from src.utils import sanitize_prompt; assert sanitize_prompt('Hello World! 🌅') == 'hello-world'; print('OK')"` → "OK"
      2. Run `python -c "from src.utils import sanitize_prompt; r = sanitize_prompt('a' * 100); assert len(r) <= 50; print('OK')"` → "OK"
      3. Run `python -c "from src.utils import sanitize_prompt; r = sanitize_prompt('---!!!---'); assert r == 'unnamed'; print('OK')"` → "OK"
    Expected Result: All 3 assertions pass
    Failure Indicators: AssertionError on any sanitization rule
    Evidence: .sisyphus/evidence/task-3-sanitization.txt

  Scenario: Directory creation
    Tool: Bash
    Preconditions: src/utils.py implemented
    Steps:
      1. Run `python -c "from src.utils import ensure_output_dir; import os; p = ensure_output_dir('/tmp/test-output', 'test-prompt'); assert os.path.isdir(p); print(p)"`
      2. Assert exit code 0 and output contains "/tmp/test-output/test-prompt"
      3. Run `rm -rf /tmp/test-output` (cleanup)
    Expected Result: Directory created at correct path
    Failure Indicators: OSError, path mismatch
    Evidence: .sisyphus/evidence/task-3-directory.txt
  ```

  **Commit**: YES
  - Message: `feat(utils): add filename sanitization, logging, and retry utilities`
  - Files: src/utils.py, tests/test_utils.py
  - Pre-commit: `pytest tests/test_utils.py -v`

- [ ] 4. Batch File Parser — .txt and .json Support + TDD

  **What to do**:
  - **RED**: Write tests first in `tests/test_batch.py`:
    - Parse `.txt` file: one prompt per line, skip empty lines, strip whitespace
    - Parse `.json` file: array of objects `[{"prompt": "...", "count": 2, "aspect_ratio": "16:9"}, ...]`
    - Parse `.json` file: simple array of strings `["prompt 1", "prompt 2"]`
    - Handle empty file → return empty list
    - Handle file with only comments (lines starting with `#`) → skip comments
    - Handle non-existent file → clear FileNotFoundError
    - Handle unsupported extension (`.csv`) → clear error message
  - Create test fixtures in `tests/fixtures/`:
    - `sample_prompts.txt` — 3 prompts, 1 empty line, 1 comment line
    - `sample_prompts.json` — 3 prompt objects with varying settings
    - `simple_prompts.json` — simple string array
  - **GREEN**: Add to `src/config.py` (or separate `src/batch.py` if cleaner):
    - `parse_batch_file(path: str) -> list[dict]` — Detect format by extension, parse accordingly
    - Each prompt dict: `{"prompt": str, "count": int|None, "aspect_ratio": str|None, "model": str|None}`
    - For `.txt`: each line becomes `{"prompt": line}` (other fields None = use defaults)
    - For `.json`: parse as-is, validate required "prompt" field
  - **REFACTOR**: Clean up, ensure consistent return type
  - Run `pytest tests/test_batch.py -v` → all pass

  **Must NOT do**:
  - Don't support CSV format (over-engineering for this use case)
  - Don't add prompt validation/filtering (send exactly what's in the file)
  - Don't support nested JSON structures — keep it flat
  - Don't auto-detect encoding — assume UTF-8

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple file parsing with clear TDD — no browser, no complex logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 2, 3 — after Task 1)
  - **Parallel Group**: Wave 1 (with Tasks 2, 3)
  - **Blocks**: Tasks 7, 10
  - **Blocked By**: Task 1

  **References**:

  **Pattern References**:
  - Python `json.load()` for JSON parsing
  - Standard file reading with `open(path, 'r', encoding='utf-8')`

  **WHY Each Reference Matters**:
  - JSON parsing handles both simple arrays and objects-with-settings
  - UTF-8 encoding covers most user scenarios including Unicode prompts

  **Acceptance Criteria**:
  - [ ] `tests/test_batch.py` has ≥7 test cases
  - [ ] `pytest tests/test_batch.py -v` → all PASS
  - [ ] Test fixture files exist in `tests/fixtures/`
  - [ ] `.txt` parsing handles empty lines, comments, whitespace correctly
  - [ ] `.json` parsing handles both string arrays and object arrays

  **QA Scenarios**:

  ```
  Scenario: Parse .txt batch file
    Tool: Bash
    Preconditions: tests/fixtures/sample_prompts.txt exists with 3 prompts + 1 comment + 1 empty line
    Steps:
      1. Run `python -c "from src.config import parse_batch_file; prompts = parse_batch_file('tests/fixtures/sample_prompts.txt'); assert len(prompts) == 3; print(f'Parsed {len(prompts)} prompts'); print(prompts[0])"`
      2. Assert exit code 0, output shows 3 prompts parsed, first prompt has "prompt" key
    Expected Result: Exactly 3 prompts parsed (comments and blanks skipped)
    Failure Indicators: Wrong count, comment lines included, empty strings in results
    Evidence: .sisyphus/evidence/task-4-txt-parse.txt

  Scenario: Parse .json batch file with settings
    Tool: Bash
    Preconditions: tests/fixtures/sample_prompts.json exists with objects having prompt + optional settings
    Steps:
      1. Run `python -c "from src.config import parse_batch_file; prompts = parse_batch_file('tests/fixtures/sample_prompts.json'); assert len(prompts) >= 2; assert 'prompt' in prompts[0]; print('JSON OK')"`
      2. Assert exit code 0
    Expected Result: JSON prompts parsed with settings preserved
    Failure Indicators: KeyError, JSON decode error
    Evidence: .sisyphus/evidence/task-4-json-parse.txt

  Scenario: Invalid file extension error
    Tool: Bash
    Preconditions: None
    Steps:
      1. Run `python -c "from src.config import parse_batch_file; parse_batch_file('test.csv')"` → should raise ValueError
      2. Assert exit code != 0 and stderr mentions "unsupported" or "format"
    Expected Result: Clear error about unsupported file format
    Failure Indicators: Silent failure or generic error
    Evidence: .sisyphus/evidence/task-4-invalid-ext.txt
  ```

  **Commit**: YES
  - Message: `feat(batch): add batch file parser for txt and json formats`
  - Files: src/config.py (or src/batch.py), tests/test_batch.py, tests/fixtures/*
  - Pre-commit: `pytest tests/test_batch.py -v`

- [ ] 5. Browser Session Manager — Chrome Profile Copy, Playwright Persistent Context

  **What to do**:
  - Implement `src/browser.py`:
    - `BrowserManager` class with:
      - `__init__(config: dict)` — Store config (chrome_profile_path, headless, user_agent settings)
      - `_find_chrome_profile() -> str` — Auto-detect Chrome profile dir: check `~/.config/google-chrome/Default`, `~/.config/chromium/Default`, `~/.config/google-chrome-beta/Default`. If not found, print clear error message with instructions.
      - `_copy_profile_to_temp(profile_path: str) -> str` — Copy Chrome profile to temp directory using `shutil.copytree`. This avoids locking the user's real Chrome. Return temp path. Log the temp path for debugging.
      - `launch() -> tuple[BrowserContext, Page]` — Launch Playwright with:
        - `playwright.chromium.launch_persistent_context(temp_profile_path, channel="chrome", headless=config.headless, ...)`
        - `viewport={"width": 1920, "height": 1080}`
        - `args=["--disable-blink-features=AutomationControlled"]` to reduce bot detection
        - `slow_mo=50` for natural interaction speed
      - `close()` — Close context, cleanup temp profile directory
      - Context manager support (`__aenter__`, `__aexit__`) for `async with BrowserManager(config) as (context, page):`
  - Handle case where Chrome is not installed: detect and print helpful error with install instructions
  - Handle case where profile directory doesn't exist: first-run guide (launch Chrome, log into Google, close Chrome, then retry)
  - Write basic test in `tests/test_browser.py`: test `_find_chrome_profile()` returns path or raises, test `_copy_profile_to_temp()` creates temp dir (can use a mock/dummy dir)

  **Must NOT do**:
  - Don't install `rebrowser-playwright` or stealth forks
  - Don't store or handle Google credentials directly
  - Don't attempt to automate Google login
  - Don't use headless mode by default (explicit user flag only)
  - Don't persist the temp profile copy between runs

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Playwright persistent context setup has nuances — profile copying, async context manager, error handling for missing Chrome. Requires careful implementation.
  - **Skills**: [`playwright`]
    - `playwright`: Core browser automation framework — needed for correct `launch_persistent_context` API usage
  - **Skills Evaluated but Omitted**:
    - `git-master`: Simple commit at end

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 6)
  - **Parallel Group**: Wave 2 (with Tasks 6, 7 — but 7 depends on 5+6)
  - **Blocks**: Task 7
  - **Blocked By**: Tasks 2, 3

  **References**:

  **Pattern References**:
  - Playwright `launch_persistent_context()` docs — the ONLY way to reuse Chrome login sessions
  - `shutil.copytree()` for profile directory copying
  - Python `tempfile.mkdtemp()` for temp directory creation

  **External References**:
  - Playwright Python docs: `BrowserType.launch_persistent_context(user_data_dir, ...)`
  - Chrome profile paths on Linux: `~/.config/google-chrome/Default`

  **WHY Each Reference Matters**:
  - `launch_persistent_context` is the single most critical API — using `browser.launch()` would lose all cookies/login state
  - Profile must be COPIED, not used directly — Chrome locks the profile when open, causing conflicts

  **Acceptance Criteria**:
  - [ ] `src/browser.py` exists with `BrowserManager` class
  - [ ] Chrome profile auto-detection works for standard Linux paths
  - [ ] Profile is copied to temp directory (original untouched)
  - [ ] Async context manager pattern works: `async with BrowserManager(config) as (ctx, page):`
  - [ ] Clear error message when Chrome not installed or profile not found
  - [ ] `pytest tests/test_browser.py -v` → PASS

  **QA Scenarios**:

  ```
  Scenario: Chrome profile detection
    Tool: Bash
    Preconditions: Chrome may or may not be installed
    Steps:
      1. Run `python -c "from src.browser import BrowserManager; bm = BrowserManager({'headless': False}); path = bm._find_chrome_profile(); print(f'Profile: {path}')"` 
      2. If Chrome installed: assert exit code 0, output contains a valid path
      3. If Chrome NOT installed: assert exit code != 0, output contains helpful error message mentioning "install Chrome" or "Chrome profile not found"
    Expected Result: Either finds profile or gives clear instructions
    Failure Indicators: Cryptic error, empty path, crash without message
    Evidence: .sisyphus/evidence/task-5-profile-detect.txt

  Scenario: Profile copy to temp directory
    Tool: Bash
    Preconditions: Create a dummy Chrome profile dir for testing
    Steps:
      1. Run `mkdir -p /tmp/test-chrome-profile/Default && echo "test" > /tmp/test-chrome-profile/Default/test.txt`
      2. Run `python -c "from src.browser import BrowserManager; import os; bm = BrowserManager({'chrome_profile_path': '/tmp/test-chrome-profile/Default', 'headless': False}); tp = bm._copy_profile_to_temp('/tmp/test-chrome-profile/Default'); assert os.path.isdir(tp); assert os.path.exists(os.path.join(tp, 'test.txt')); print(f'Copied to: {tp}')"`
      3. Assert temp directory was created with copied contents
      4. Cleanup: `rm -rf /tmp/test-chrome-profile`
    Expected Result: Profile copied successfully to temp dir
    Failure Indicators: PermissionError, path not found, files not copied
    Evidence: .sisyphus/evidence/task-5-profile-copy.txt
  ```

  **Commit**: YES
  - Message: `feat(browser): add Chrome profile management and Playwright session`
  - Files: src/browser.py, tests/test_browser.py
  - Pre-commit: `pytest tests/ -v`

- [ ] 6. Selector Abstraction Layer — All Flow UI Selectors in One Module

  **What to do**:
  - Implement `src/selectors.py`:
    - `FlowSelectors` class (or dataclass) with ALL Google Flow UI selectors as named constants:
      - `PROMPT_INPUT` — The text input area where prompts are typed
      - `GENERATE_BUTTON` — The sparkle/arrow button to trigger generation
      - `SETTINGS_PANEL_TRIGGER` — Element to click to open settings (e.g., model name near prompt)
      - `ASPECT_RATIO_SELECTOR` — Aspect ratio dropdown/buttons in settings
      - `IMAGE_COUNT_SELECTOR` — Number of images to generate selector
      - `MODEL_SELECTOR` — AI model selection (Nano Banana 2, Imagen 4, etc.)
      - `GENERATED_IMAGE_CONTAINER` — Container holding generated image results
      - `GENERATED_IMAGE_ITEM` — Individual generated image element
      - `IMAGE_DOWNLOAD_BUTTON` — Download button on image hover/menu
      - `IMAGE_DOWNLOAD_MENU` — Three-dots menu on image hover
      - `LOADING_INDICATOR` — Spinner/progress indicator during generation
      - `GENERATION_COMPLETE` — Signal that generation is done (images visible, spinner gone)
      - `CAPTCHA_OVERLAY` — CAPTCHA/challenge detection selector
      - `CONSENT_DIALOG` — "I understand" / terms acceptance dialog
      - `CONSENT_ACCEPT_BUTTON` — Button to dismiss consent dialog
      - `SAFETY_FILTER_WARNING` — Content policy rejection message
      - `QUOTA_EXCEEDED_DIALOG` — Rate limit / quota exceeded message
      - `ERROR_MESSAGE` — General error/warning message display
    - Each selector should have:
      - `css: str` — Primary CSS selector
      - `text: str | None` — Optional text-based fallback selector (more resilient to UI changes)
      - `aria: str | None` — Optional aria-label selector (accessibility-based, stable)
      - `description: str` — Human-readable description for debugging
    - **CRITICAL**: The implementing agent MUST explore Google Flow's actual UI using Playwright to discover correct selectors. This task requires:
      1. Launch browser, navigate to `https://labs.google/flow`
      2. Use Playwright's `.locator()` and DevTools to inspect each UI element
      3. Record actual selectors found — DO NOT guess or use placeholder selectors
      4. If any element cannot be found, document it clearly with the best-effort selector and mark as `# NEEDS VERIFICATION`
    - Create `get_selector(name: str, strategy: str = "css") -> str` utility to retrieve selectors by name and strategy

  **Must NOT do**:
  - Don't hardcode selectors directly in flow.py — ALL selectors MUST live in selectors.py
  - Don't guess selectors without inspecting the actual UI
  - Don't create overly complex selector chains — prefer simple, readable selectors
  - Don't use XPath (CSS selectors and text/aria selectors are more maintainable)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Single file with structured data — the key challenge is DISCOVERING the selectors via Playwright inspection, but the code itself is straightforward
  - **Skills**: [`playwright`]
    - `playwright`: Needed to launch browser and inspect Google Flow UI to discover real selectors
  - **Skills Evaluated but Omitted**:
    - None — Playwright is the only skill needed

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 5)
  - **Parallel Group**: Wave 2 (with Task 5)
  - **Blocks**: Tasks 7, 8, 9
  - **Blocked By**: Task 1

  **References**:

  **Pattern References**:
  - Python dataclass or named constants for structured selector storage
  - Playwright selector strategies: CSS, text, aria-label, role

  **External References**:
  - Google Flow UI: `https://labs.google/flow` — Must be explored live by the implementing agent
  - Playwright selectors guide: CSS, text-based, and role-based selectors
  - Feb 2026 Flow UI redesign blog: `https://blog.google/innovation-and-ai/models-and-research/google-labs/flow-updates-february-2026/`

  **WHY Each Reference Matters**:
  - The actual Flow UI must be inspected to get REAL selectors — Google can change these at any time
  - Multiple selector strategies (CSS + text + aria) provide fallback resilience
  - The Feb 2026 redesign means older tutorials/screenshots are outdated

  **Acceptance Criteria**:
  - [ ] `src/selectors.py` exists with `FlowSelectors` class
  - [ ] At least 15 named selectors covering: prompt input, generate button, settings, images, download, CAPTCHA, consent, errors
  - [ ] Each selector has CSS + at least one fallback (text or aria)
  - [ ] `python -c "from src.selectors import FlowSelectors; print(FlowSelectors.PROMPT_INPUT)"` → prints selector info
  - [ ] Comments explain what each selector targets and how it was discovered

  **QA Scenarios**:

  ```
  Scenario: Selector module loads and has all required selectors
    Tool: Bash
    Preconditions: src/selectors.py implemented
    Steps:
      1. Run `python -c "
from src.selectors import FlowSelectors
required = ['PROMPT_INPUT', 'GENERATE_BUTTON', 'SETTINGS_PANEL_TRIGGER', 'GENERATED_IMAGE_CONTAINER', 'IMAGE_DOWNLOAD_BUTTON', 'LOADING_INDICATOR', 'CAPTCHA_OVERLAY', 'CONSENT_DIALOG', 'SAFETY_FILTER_WARNING']
for sel in required:
    assert hasattr(FlowSelectors, sel), f'Missing: {sel}'
print(f'All {len(required)} required selectors present')
"`
      2. Assert exit code 0
    Expected Result: All 9 critical selectors exist
    Failure Indicators: AttributeError for any missing selector
    Evidence: .sisyphus/evidence/task-6-selectors.txt

  Scenario: Selectors have fallback strategies
    Tool: Bash
    Preconditions: src/selectors.py implemented
    Steps:
      1. Run `python -c "from src.selectors import FlowSelectors; sel = FlowSelectors.PROMPT_INPUT; assert sel.css, 'No CSS selector'; assert sel.text or sel.aria, 'No fallback selector'; print(f'CSS: {sel.css}, Fallback: {sel.text or sel.aria}')"`
      2. Assert exit code 0
    Expected Result: PROMPT_INPUT has CSS + at least one fallback
    Failure Indicators: Missing CSS or missing all fallbacks
    Evidence: .sisyphus/evidence/task-6-fallback.txt
  ```

  **Commit**: YES
  - Message: `feat(selectors): add UI selector abstraction layer for Google Flow`
  - Files: src/selectors.py
  - Pre-commit: `python -c "from src.selectors import FlowSelectors"`

- [ ] 7. Google Flow Page Interaction Layer — Navigate, Prompt, Settings, Generate, Wait

  **What to do**:
  - Implement `src/flow.py`:
    - `FlowPage` class wrapping a Playwright `Page` object:
      - `__init__(page: Page, selectors: FlowSelectors, config: dict)` — Store page, selectors, config
      - `async navigate()` — Go to `https://labs.google/flow`, wait for page to fully load, handle any consent/terms dialogs by auto-dismissing
      - `async dismiss_consent()` — Detect and click through any "I understand" / experimental AI terms dialogs. Use selectors from `FlowSelectors.CONSENT_DIALOG` and `CONSENT_ACCEPT_BUTTON`. Safe to call multiple times (no-op if no dialog).
      - `async enter_prompt(prompt: str)` — Click on prompt input area, clear any existing text, type prompt with human-like delays (random 50-150ms between keystrokes from config). Use `human_delay()` from utils.
      - `async configure_settings(count: int = None, aspect_ratio: str = None, model: str = None)` — Open settings panel, set requested options. Only modify settings that are explicitly provided (None = leave at current).
      - `async click_generate()` — Click the generate button with human-like pre-click delay (200-500ms). Add random mouse movement to button area before click.
      - `async wait_for_generation(timeout: int = None) -> bool` — Wait for loading indicator to appear, then wait for it to disappear (generation complete). Use config `generation_timeout` (default 120s). Return True if successful, False if timed out.
      - `async detect_captcha() -> bool` — Check if CAPTCHA overlay appeared. If detected, log warning and return True.
      - `async handle_captcha()` — Print clear message to terminal: "⚠️ CAPTCHA detected! Please solve it in the browser window. Press Enter when done..." Wait for user terminal input, then verify CAPTCHA is gone.
      - `async detect_safety_filter() -> bool` — Check if prompt was rejected by safety filter. Return True if rejected.
      - `async detect_quota_exceeded() -> bool` — Check for rate limit / quota exceeded dialog.
      - `async get_generated_images() -> list[ElementHandle]` — After generation completes, locate all generated image elements. Return list of image element handles.
  - Implement human-like interaction patterns throughout:
    - Random delay before each action (200-500ms)
    - Natural typing speed with random per-character delay
    - Occasional typo correction (type wrong char, backspace, correct — 5% chance) for enhanced human-likeness
    - Mouse movement to target element before clicking (not instant teleportation)
  - Handle navigation errors: if Flow page doesn't load, retry once, then raise with clear error

  **Must NOT do**:
  - Don't handle image downloading (that's Task 8)
  - Don't implement retry/backoff logic here (that's Task 9 — use the retry decorator from utils)
  - Don't modify or enhance the user's prompt text in any way
  - Don't hardcode selectors — ALL selector access must go through FlowSelectors from selectors.py

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex async Playwright interactions with Google Flow — requires understanding page load states, dynamic content, timing, anti-bot measures. Core automation logic.
  - **Skills**: [`playwright`]
    - `playwright`: Essential — this IS the Playwright automation layer
  - **Skills Evaluated but Omitted**:
    - `dev-browser`: Playwright skill is more direct for this code-writing task

  **Parallelization**:
  - **Can Run In Parallel**: NO
  - **Parallel Group**: Wave 2 (sequential after Tasks 5, 6)
  - **Blocks**: Tasks 8, 9, 10
  - **Blocked By**: Tasks 5, 6

  **References**:

  **Pattern References**:
  - `src/selectors.py` (Task 6) — ALL selectors must be accessed from here, never hardcoded
  - `src/utils.py:human_delay()` (Task 3) — Use for all human-like timing
  - `src/browser.py:BrowserManager` (Task 5) — Page object comes from browser manager

  **External References**:
  - Playwright Page API: `page.goto()`, `page.locator()`, `page.wait_for_selector()`, `page.keyboard.type()`
  - Playwright `locator.click()`, `locator.fill()`, `locator.type()` — different typing methods
  - Google Flow: `https://labs.google/flow` — target page

  **WHY Each Reference Matters**:
  - Selectors module provides all UI element references — flow.py should NEVER define selectors
  - `page.type()` sends individual keystrokes (human-like) vs `page.fill()` which sets value instantly (detectable)
  - Human delay functions prevent bot detection from rapid, machine-like interactions

  **Acceptance Criteria**:
  - [ ] `src/flow.py` exists with `FlowPage` class and all listed methods
  - [ ] All selector access goes through `FlowSelectors` — no hardcoded CSS/text selectors in flow.py
  - [ ] Human-like delays are used for all interactions (typing, clicking)
  - [ ] Consent dialog handling works (auto-dismiss)
  - [ ] CAPTCHA detection pauses and alerts user
  - [ ] Safety filter detection returns clear boolean
  - [ ] `wait_for_generation()` respects configurable timeout

  **QA Scenarios**:

  ```
  Scenario: FlowPage class loads and has all required methods
    Tool: Bash
    Preconditions: src/flow.py implemented
    Steps:
      1. Run `python -c "
from src.flow import FlowPage
import inspect
required_methods = ['navigate', 'dismiss_consent', 'enter_prompt', 'configure_settings', 'click_generate', 'wait_for_generation', 'detect_captcha', 'handle_captcha', 'detect_safety_filter', 'get_generated_images']
for method in required_methods:
    assert hasattr(FlowPage, method), f'Missing method: {method}'
    assert callable(getattr(FlowPage, method)), f'Not callable: {method}'
print(f'All {len(required_methods)} methods present')
"`
      2. Assert exit code 0
    Expected Result: All 10 required methods exist on FlowPage class
    Failure Indicators: AttributeError for missing methods
    Evidence: .sisyphus/evidence/task-7-flow-methods.txt

  Scenario: No hardcoded selectors in flow.py
    Tool: Bash (grep)
    Preconditions: src/flow.py implemented
    Steps:
      1. Search src/flow.py for hardcoded CSS selectors: patterns like `".class-name"`, `"#id"`, `"[attribute]"` that aren't from FlowSelectors
      2. Assert: flow.py imports from src.selectors and ALL element access goes through FlowSelectors
      3. Run `grep -c "FlowSelectors" src/flow.py` → should be ≥5 (used for multiple elements)
    Expected Result: Zero hardcoded selectors; all access via FlowSelectors
    Failure Indicators: Found raw CSS strings not from selectors module
    Evidence: .sisyphus/evidence/task-7-no-hardcoded.txt
  ```

  **Commit**: YES
  - Message: `feat(flow): add Google Flow page interaction layer`
  - Files: src/flow.py
  - Pre-commit: `pytest tests/ -v`

- [ ] 8. Image Downloader — Detect Images, Download All, Organized Save

  **What to do**:
  - Implement `src/downloader.py`:
    - `ImageDownloader` class:
      - `__init__(config: dict, utils: module)` — Store output config and utils reference
      - `async download_all_images(page: Page, flow: FlowPage, prompt: str) -> list[str]` — Main method:
        1. Call `flow.get_generated_images()` to get image elements
        2. For each image element, download the image
        3. Save to organized directory structure
        4. Return list of saved file paths
      - `async _download_single_image(page: Page, image_element, index: int, slug: str, date_str: str) -> str` — Download one image:
        - Strategy 1: Try extracting image `src` attribute (if it's a direct URL) → fetch with `page.request.get(url)` → save bytes
        - Strategy 2: Try right-click → "Download" menu → capture via `page.expect_download()` → `download.save_as(path)`
        - Strategy 3: Try clicking the download button on the image card → capture download
        - Strategy 4: Screenshot the image element as fallback (lower quality but always works)
        - Log which strategy was used for debugging
      - `_build_save_path(base_dir: str, slug: str, date_str: str, index: int, ext: str) -> str` — Build full path: `{base_dir}/{slug}/{slug}_{date}_{NNN}.{ext}`
      - `_detect_image_format(data: bytes) -> str` — Detect PNG/JPEG/WebP from magic bytes
  - Create output directory if not exists
  - Handle duplicate filenames: if file exists, increment index until unique
  - Log each saved image path and file size
  - Write unit tests in `tests/test_downloader.py`:
    - Test `_build_save_path()` produces correct paths
    - Test `_detect_image_format()` identifies PNG, JPEG, WebP from magic bytes
    - Test duplicate filename handling (increment index)

  **Must NOT do**:
  - Don't process/resize/convert images — save exactly what was downloaded
  - Don't add watermarks or metadata
  - Don't attempt to download video content (images only)
  - Don't use external HTTP libraries (requests, httpx) — use Playwright's built-in `page.request`

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Multiple download strategies needed, handling browser downloads via Playwright, binary format detection, file I/O. Requires understanding Playwright download API.
  - **Skills**: [`playwright`]
    - `playwright`: Needed for `page.expect_download()`, `download.save_as()`, `page.request.get()` APIs
  - **Skills Evaluated but Omitted**:
    - None additional needed

  **Parallelization**:
  - **Can Run In Parallel**: NO (needs Task 7 complete)
  - **Parallel Group**: Wave 3 (with Task 9, but 9 may depend on 8)
  - **Blocks**: Tasks 9, 10, 12
  - **Blocked By**: Tasks 7, 3

  **References**:

  **Pattern References**:
  - `src/utils.py:sanitize_prompt()` (Task 3) — For generating slug from prompt
  - `src/utils.py:generate_filename()` (Task 3) — For building filenames
  - `src/utils.py:ensure_output_dir()` (Task 3) — For creating output directories
  - `src/flow.py:FlowPage.get_generated_images()` (Task 7) — Source of image elements
  - `src/selectors.py:FlowSelectors.IMAGE_DOWNLOAD_BUTTON` (Task 6) — Download button selector

  **External References**:
  - Playwright Download API: `page.expect_download()`, `download.save_as(path)`, `download.path()`
  - Playwright Request API: `page.request.get(url)` for fetching image URLs directly
  - PNG magic bytes: `\x89PNG\r\n\x1a\n`, JPEG: `\xff\xd8\xff`, WebP: `RIFF....WEBP`

  **WHY Each Reference Matters**:
  - Multiple download strategies are needed because Google Flow may serve images differently (blob URLs, CDN URLs, canvas)
  - Format detection ensures correct file extension regardless of how the image was obtained
  - Utils functions ensure consistent naming/directory structure across the tool

  **Acceptance Criteria**:
  - [ ] `src/downloader.py` exists with `ImageDownloader` class
  - [ ] Multiple download strategies implemented (URL fetch, browser download, screenshot fallback)
  - [ ] Images saved to correct directory: `{output_dir}/{slug}/{slug}_{date}_{NNN}.{ext}`
  - [ ] Duplicate filenames handled by incrementing index
  - [ ] Image format detected from magic bytes (correct extension)
  - [ ] `pytest tests/test_downloader.py -v` → PASS

  **QA Scenarios**:

  ```
  Scenario: Save path generation
    Tool: Bash
    Preconditions: src/downloader.py implemented
    Steps:
      1. Run `python -c "
from src.downloader import ImageDownloader
dl = ImageDownloader({'output_dir': 'output'})
path = dl._build_save_path('output', 'sunset-mountains', '2026-03-20', 1, 'png')
assert path == 'output/sunset-mountains/sunset-mountains_2026-03-20_001.png', f'Got: {path}'
print(f'Path: {path}')
"`
      2. Assert exit code 0 and correct path format
    Expected Result: Path matches expected naming convention
    Failure Indicators: Wrong path format, wrong zero-padding
    Evidence: .sisyphus/evidence/task-8-save-path.txt

  Scenario: Image format detection
    Tool: Bash
    Preconditions: src/downloader.py implemented
    Steps:
      1. Run `python -c "
from src.downloader import ImageDownloader
dl = ImageDownloader({})
assert dl._detect_image_format(b'\x89PNG\r\n\x1a\n') == 'png'
assert dl._detect_image_format(b'\xff\xd8\xff') == 'jpeg'
assert dl._detect_image_format(b'RIFF....WEBP') == 'webp'
print('Format detection OK')
"`
      2. Assert exit code 0
    Expected Result: All three formats correctly identified
    Failure Indicators: Wrong format returned for any magic bytes
    Evidence: .sisyphus/evidence/task-8-format-detect.txt
  ```

  **Commit**: YES
  - Message: `feat(download): add image detection, download, and organized save`
  - Files: src/downloader.py, tests/test_downloader.py
  - Pre-commit: `pytest tests/ -v`

- [ ] 9. Error Handling & Resilience — CAPTCHA, Consent, Safety Filter, Retry

  **What to do**:
  - Enhance `src/flow.py` with resilience wrappers:
    - `async generate_with_resilience(prompt: str, settings: dict) -> bool` — Orchestrator method that wraps the full generation flow with error handling:
      1. Enter prompt (with retry on input failure)
      2. Configure settings (skip if none specified)
      3. Click generate
      4. Check for CAPTCHA → if detected, call `handle_captcha()` (pause for user), then retry generate
      5. Check for safety filter → if rejected, log warning, return False (skip this prompt)
      6. Check for quota exceeded → if detected, log warning, wait `config.quota_wait_time` (default 60s), retry
      7. Wait for generation → if timeout, retry up to `config.max_retries` times with exponential backoff
      8. On success, return True
  - Add `@retry_with_backoff` decorator from `src/utils.py` to key operations
  - Implement consent dialog handling in navigation flow:
    - After `navigate()`, always call `dismiss_consent()` to handle any dialogs
    - `dismiss_consent()` should be idempotent — safe to call even if no dialog present
  - Add inter-generation delay:
    - After each successful generation + download, wait `config.delay_between_generations` seconds (default 10s)
    - Add random jitter: ±30% of the configured delay
  - Add graceful shutdown handling:
    - Catch `KeyboardInterrupt` in main loop — save progress, close browser cleanly, print summary
  - Write tests in `tests/test_resilience.py`:
    - Test retry decorator behavior with mock functions
    - Test delay jitter is within expected range
    - Test graceful shutdown saves state (mock)

  **Must NOT do**:
  - Don't implement proxy rotation or IP masking
  - Don't install stealth/anti-detection libraries (rebrowser-playwright, etc.)
  - Don't auto-solve CAPTCHAs — always pause for user manual solving
  - Don't auto-modify prompts that hit safety filters
  - Don't implement sophisticated bot detection evasion beyond human-like delays

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Complex error handling orchestration — CAPTCHA detection/pausing, safety filter detection, quota handling, retry with backoff, graceful shutdown. Multiple interacting error states.
  - **Skills**: [`playwright`]
    - `playwright`: Needed for browser state detection (CAPTCHA overlays, dialog selectors)
  - **Skills Evaluated but Omitted**:
    - None additional

  **Parallelization**:
  - **Can Run In Parallel**: YES (can start with Task 8 in Wave 3)
  - **Parallel Group**: Wave 3 (with Task 8)
  - **Blocks**: Tasks 10, 12
  - **Blocked By**: Tasks 7, 3

  **References**:

  **Pattern References**:
  - `src/utils.py:retry_with_backoff` (Task 3) — Retry decorator to wrap operations
  - `src/utils.py:human_delay()` (Task 3) — For inter-generation delays with jitter
  - `src/flow.py:FlowPage.detect_captcha()` (Task 7) — CAPTCHA detection method
  - `src/flow.py:FlowPage.detect_safety_filter()` (Task 7) — Safety filter detection
  - `src/selectors.py:FlowSelectors.CAPTCHA_OVERLAY` (Task 6) — CAPTCHA selector
  - `src/selectors.py:FlowSelectors.QUOTA_EXCEEDED_DIALOG` (Task 6) — Quota selector

  **WHY Each Reference Matters**:
  - Retry decorator from utils ensures consistent retry behavior across all operations
  - CAPTCHA/safety detection from flow.py provides the detection layer; this task adds the HANDLING layer
  - Human delays with jitter make the tool appear more natural between generations

  **Acceptance Criteria**:
  - [ ] `generate_with_resilience()` handles CAPTCHA (pause + alert user)
  - [ ] Safety filter rejections are logged and skipped (not retried)
  - [ ] Quota exceeded triggers configurable wait then retry
  - [ ] Generation timeout triggers exponential backoff retry (up to max_retries)
  - [ ] Inter-generation delay has random jitter (±30%)
  - [ ] `KeyboardInterrupt` is caught cleanly — progress saved, browser closed, summary printed
  - [ ] `pytest tests/test_resilience.py -v` → PASS

  **QA Scenarios**:

  ```
  Scenario: Retry decorator with backoff
    Tool: Bash
    Preconditions: src/utils.py retry decorator and tests implemented
    Steps:
      1. Run `python -c "
import time
from src.utils import retry_with_backoff
call_count = 0
@retry_with_backoff(max_retries=3, base_delay=0.1)
def flaky():
    global call_count
    call_count += 1
    if call_count < 3:
        raise Exception('fail')
    return 'success'
result = flaky()
assert result == 'success'
assert call_count == 3
print(f'Retried {call_count} times, result: {result}')
"`
      2. Assert exit code 0
    Expected Result: Function called 3 times, succeeds on 3rd try
    Failure Indicators: Exception raised instead of retry, wrong call count
    Evidence: .sisyphus/evidence/task-9-retry.txt

  Scenario: Delay jitter within range
    Tool: Bash
    Preconditions: Human delay function implemented
    Steps:
      1. Run `python -c "
import time
from src.utils import human_delay
start = time.time()
human_delay(100, 200)
elapsed = (time.time() - start) * 1000
assert 80 <= elapsed <= 250, f'Delay out of range: {elapsed}ms'
print(f'Delay: {elapsed:.0f}ms (expected 100-200ms)')
"`
      2. Assert elapsed time within range (with small tolerance for scheduling)
    Expected Result: Delay between 80-250ms (100-200 target + tolerance)
    Failure Indicators: Delay way outside range (instant or > 500ms)
    Evidence: .sisyphus/evidence/task-9-delay.txt
  ```

  **Commit**: YES
  - Message: `feat(resilience): add CAPTCHA detection, consent handling, retry logic`
  - Files: src/flow.py (updates), src/utils.py (updates if needed), tests/test_resilience.py
  - Pre-commit: `pytest tests/ -v`

- [ ] 10. Session Summary & Logging — Report Generation, Session Log Files

  **What to do**:
  - Implement `src/reporter.py`:
    - `SessionReporter` class:
      - `__init__(config: dict)` — Initialize with config, start timestamp, empty results list
      - `record_success(prompt: str, images: list[str], elapsed: float)` — Record successful generation
      - `record_failure(prompt: str, error: str, retries: int)` — Record failed generation
      - `record_skip(prompt: str, reason: str)` — Record skipped prompt (safety filter, etc.)
      - `get_summary() -> dict` — Return summary stats: total, success, failed, skipped, total images, total time
      - `print_summary()` — Print formatted summary to terminal:
        ```
        ═══════════════════════════════════════════
        Session Summary — 2026-03-20 14:30
        ═══════════════════════════════════════════
        Total Prompts:  10
        ✅ Successful:   8 (32 images)
        ❌ Failed:       1
        ⏭️  Skipped:     1 (safety filter)
        ⏱️  Total Time:  12m 34s
        📁 Output:      output/
        📋 Log:         logs/session_2026-03-20_143000.log
        ═══════════════════════════════════════════
        ```
      - `save_log(log_dir: str = "logs")` — Save detailed JSON log file: `logs/session_{date}_{time}.json` with all prompts, results, paths, errors, timing
  - Integrate into `generate.py` main flow:
    - Create reporter at start of session
    - After each generation: record result
    - At end (or on KeyboardInterrupt): print summary + save log
  - Wire up the full pipeline in `generate.py`:
    - Parse args → Load config → Create BrowserManager → Create FlowPage → For each prompt: generate_with_resilience → download_all_images → record result → Inter-generation delay → Print summary → Save log
  - Handle batch mode: loop through all prompts from batch file
  - Handle single mode: process one prompt from --prompt arg

  **Must NOT do**:
  - Don't add log rotation or log management
  - Don't use structured logging frameworks (loguru, structlog)
  - Don't add email/webhook notifications on completion
  - Don't create a TUI progress bar (simple print statements only)
  - Don't add scheduling or daemon mode

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Reporter is straightforward data collection + formatting. The main wiring of generate.py is connecting existing modules.
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `playwright`: Not needed — this task is pure Python, no browser interaction

  **Parallelization**:
  - **Can Run In Parallel**: YES (reporter can be built in parallel with Task 11)
  - **Parallel Group**: Wave 4 (with Tasks 11)
  - **Blocks**: Task 12
  - **Blocked By**: Tasks 8, 9, 2, 4

  **References**:

  **Pattern References**:
  - `src/config.py:load_config()` (Task 2) — Load configuration
  - `src/config.py:parse_args()` (Task 2) — Parse CLI arguments
  - `src/config.py:parse_batch_file()` (Task 4) — Load batch prompts
  - `src/browser.py:BrowserManager` (Task 5) — Browser launch
  - `src/flow.py:FlowPage` (Task 7) — Page interactions
  - `src/flow.py:generate_with_resilience()` (Task 9) — Resilient generation
  - `src/downloader.py:ImageDownloader` (Task 8) — Image downloading
  - `src/utils.py:setup_logging()` (Task 3) — Logging setup

  **WHY Each Reference Matters**:
  - This task is the INTEGRATION point — it wires all previous modules together in generate.py
  - Reporter provides user-facing feedback — the only way user knows what happened in a batch

  **Acceptance Criteria**:
  - [ ] `src/reporter.py` exists with `SessionReporter` class
  - [ ] `generate.py` wires full pipeline: args → config → browser → flow → download → report
  - [ ] Single mode: `python generate.py "test"` processes one prompt
  - [ ] Batch mode: `python generate.py --batch prompts.txt` processes all prompts
  - [ ] Summary printed to terminal at end of session
  - [ ] JSON log saved to `logs/session_{date}_{time}.json`
  - [ ] `pytest tests/ -v` → all PASS

  **QA Scenarios**:

  ```
  Scenario: Reporter summary generation
    Tool: Bash
    Preconditions: src/reporter.py implemented
    Steps:
      1. Run `python -c "
from src.reporter import SessionReporter
r = SessionReporter({'output_dir': 'output'})
r.record_success('sunset', ['img1.png', 'img2.png'], 15.5)
r.record_failure('bad prompt', 'timeout', 3)
r.record_skip('nsfw prompt', 'safety filter')
summary = r.get_summary()
assert summary['total'] == 3
assert summary['successful'] == 1
assert summary['failed'] == 1
assert summary['skipped'] == 1
assert summary['total_images'] == 2
print(f'Summary: {summary}')
"`
      2. Assert exit code 0, counts match expected values
    Expected Result: Summary correctly counts success/fail/skip
    Failure Indicators: Wrong counts, KeyError
    Evidence: .sisyphus/evidence/task-10-summary.txt

  Scenario: Full pipeline CLI verification
    Tool: Bash
    Preconditions: All modules wired in generate.py
    Steps:
      1. Run `python generate.py --help` → exit code 0, shows all options
      2. Run `python generate.py --prompt "test" --dry-run` (if dry-run implemented) OR verify generate.py imports all modules without error: `python -c "import generate; print('Pipeline OK')"`
    Expected Result: CLI works, all modules imported successfully
    Failure Indicators: Import errors, missing module references
    Evidence: .sisyphus/evidence/task-10-pipeline.txt
  ```

  **Commit**: YES
  - Message: `feat(report): add session summary and log file generation`
  - Files: src/reporter.py, generate.py (full wiring), tests/test_reporter.py
  - Pre-commit: `pytest tests/ -v`

- [ ] 11. README & Documentation — Professional Guide, Setup, Usage, Troubleshooting

  **What to do**:
  - Write comprehensive `README.md`:
    - **Header**: Project name, one-line description, badges (Python version, license)
    - **Features**: Bullet list of key features with emoji icons
    - **Quick Start**: 5-step guide to get running
    - **Prerequisites**:
      - Python 3.10+
      - Google Chrome browser installed
      - Google account logged into Chrome (with Google AI Plus for full features)
      - `uv` package manager (with install instructions)
    - **Installation**:
      ```bash
      git clone https://github.com/vaskoyudha/AutomationDownloadGoogleFlowImage.git
      cd AutomationDownloadGoogleFlowImage
      uv venv
      source .venv/bin/activate
      uv pip install -r requirements.txt  # or from pyproject.toml
      playwright install chromium
      ```
    - **Chrome Profile Setup**:
      1. Open Google Chrome
      2. Log into your Google account
      3. Navigate to `labs.google/flow` and accept any terms/conditions
      4. Close Chrome completely (important!)
      5. Your profile is ready at `~/.config/google-chrome/Default`
    - **Usage Examples**:
      - Single prompt: `python generate.py --prompt "a sunset over mountains"`
      - With settings: `python generate.py --prompt "abstract art" --count 4 --aspect-ratio 16:9`
      - Batch mode: `python generate.py --batch prompts.txt`
      - Custom output: `python generate.py --prompt "cat" --output-dir ~/my-images`
      - With config: `python generate.py --config my-config.yaml --prompt "landscape"`
    - **Configuration**: Document all `config.example.yaml` options with descriptions
    - **Batch File Format**: Show .txt and .json examples
    - **Output Structure**: Visual directory tree showing naming convention
    - **Troubleshooting**:
      - "Chrome not found" — install Chrome instructions per OS
      - "Profile not found" — how to find/set Chrome profile path
      - "CAPTCHA detected" — what to do when CAPTCHA appears
      - "Safety filter" — prompt was rejected, try different wording
      - "Quota exceeded" — wait or check subscription status
      - "Generation timeout" — increase timeout in config
    - **How It Works**: Brief architecture overview for contributors
    - **License**: MIT (or user's choice)
  - Create `LICENSE` file (MIT)
  - Verify README renders correctly (valid markdown)

  **Must NOT do**:
  - Don't add badges for non-existent CI/CD pipelines
  - Don't add contributing guidelines (over-engineering for personal tool)
  - Don't write API documentation (there's no API)
  - Don't include screenshots of Google Flow (copyright concerns)

  **Recommended Agent Profile**:
  - **Category**: `writing`
    - Reason: Technical documentation — README writing, clear instructions, formatting
  - **Skills**: []
  - **Skills Evaluated but Omitted**:
    - `playwright`: Not needed for documentation writing

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 10)
  - **Parallel Group**: Wave 4 (with Task 10)
  - **Blocks**: Task 12
  - **Blocked By**: Task 1 (needs to know all features from Tasks 2-9 to document)

  **References**:

  **Pattern References**:
  - `config.example.yaml` (Task 2) — Document all config options
  - `generate.py` CLI help (Task 2) — Mirror CLI options in README
  - `tests/fixtures/sample_prompts.txt` (Task 4) — Batch file format examples
  - All `src/*.py` modules — Architecture overview reference

  **External References**:
  - GitHub README best practices: clear structure, quick start, visual examples
  - Markdown formatting: code blocks, tables, emoji for visual appeal

  **WHY Each Reference Matters**:
  - README must accurately reflect the actual CLI options and config format
  - Troubleshooting section prevents common support questions

  **Acceptance Criteria**:
  - [ ] `README.md` exists with ≥200 lines of content
  - [ ] Has sections: Features, Quick Start, Prerequisites, Installation, Usage, Configuration, Troubleshooting
  - [ ] All CLI options from `--help` are documented
  - [ ] Chrome profile setup guide is clear and step-by-step
  - [ ] Batch file format (.txt and .json) is documented with examples
  - [ ] `LICENSE` file exists

  **QA Scenarios**:

  ```
  Scenario: README completeness check
    Tool: Bash
    Preconditions: README.md written
    Steps:
      1. Run `grep -c "## " README.md` → assert ≥7 sections
      2. Run `grep "generate.py" README.md | wc -l` → assert ≥3 usage examples
      3. Run `grep "config" README.md | wc -l` → assert ≥2 config references
      4. Run `grep -i "troubleshoot" README.md` → assert exists
      5. Run `grep -i "chrome" README.md | wc -l` → assert ≥3 Chrome references
      6. Assert `LICENSE` file exists
    Expected Result: README has all required sections and references
    Failure Indicators: Missing sections, no usage examples, no troubleshooting
    Evidence: .sisyphus/evidence/task-11-readme.txt

  Scenario: README code blocks are valid
    Tool: Bash
    Preconditions: README.md exists
    Steps:
      1. Run `grep -c '```' README.md` → assert even number (all blocks closed)
      2. Run `grep 'python generate.py' README.md` → assert matches show correct CLI syntax
    Expected Result: All code blocks properly opened and closed, CLI examples accurate
    Failure Indicators: Odd number of ``` markers, wrong CLI syntax
    Evidence: .sisyphus/evidence/task-11-codeblocks.txt
  ```

  **Commit**: YES
  - Message: `docs: add comprehensive README with setup guide and usage examples`
  - Files: README.md, LICENSE
  - Pre-commit: —

- [ ] 12. Final Integration Test & Push to GitHub

  **What to do**:
  - Run full test suite: `pytest tests/ -v` → all pass
  - Run `python generate.py --help` → verify all options present
  - Run import check: `python -c "from src.config import load_config; from src.utils import sanitize_prompt; from src.browser import BrowserManager; from src.flow import FlowPage; from src.downloader import ImageDownloader; from src.reporter import SessionReporter; print('All modules OK')"`
  - Verify project structure matches plan:
    ```
    generate.py
    pyproject.toml
    config.example.yaml
    README.md
    LICENSE
    .gitignore
    src/__init__.py
    src/browser.py
    src/flow.py
    src/downloader.py
    src/selectors.py
    src/config.py
    src/utils.py
    src/reporter.py
    tests/__init__.py
    tests/test_config.py
    tests/test_utils.py
    tests/test_batch.py
    tests/test_browser.py
    tests/test_downloader.py
    tests/test_resilience.py
    tests/test_reporter.py
    tests/fixtures/sample_prompts.txt
    tests/fixtures/sample_prompts.json
    output/.gitkeep
    ```
  - Verify `.gitignore` excludes: `__pycache__/`, `.venv/`, `output/` (except .gitkeep), `logs/`, `*.log`, `.sisyphus/evidence/`
  - Run a dry-run if possible, or verify the complete flow works with the available Chrome/profile setup
  - Ensure all previous commits are pushed: `git log --oneline` → verify all task commits present
  - Final push: `git push origin main`
  - Verify repo is accessible: `git remote -v` shows correct URL

  **Must NOT do**:
  - Don't add CI/CD configuration (not requested)
  - Don't create release tags or GitHub releases
  - Don't modify any existing functionality — this is VERIFICATION only
  - Don't add new features during integration

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Integration verification requires checking all modules work together, running full test suite, verifying project structure, and final git operations
  - **Skills**: [`git-master`]
    - `git-master`: Final push to remote, verify commit history, ensure clean state

  **Parallelization**:
  - **Can Run In Parallel**: NO (must wait for ALL other tasks)
  - **Parallel Group**: Wave 4 (last task before Final Verification)
  - **Blocks**: F1, F2, F3, F4
  - **Blocked By**: Tasks 10, 11

  **References**:

  **Pattern References**:
  - All `src/*.py` modules — must all import cleanly
  - All `tests/*.py` files — must all pass
  - `pyproject.toml` — project metadata must be accurate
  - Remote: `https://github.com/vaskoyudha/AutomationDownloadGoogleFlowImage.git`

  **WHY Each Reference Matters**:
  - This task verifies the entire project is cohesive and working — it's the quality gate before final review
  - Git push ensures all work is persisted to the remote repository

  **Acceptance Criteria**:
  - [ ] `pytest tests/ -v` → ALL tests PASS, 0 failures
  - [ ] `python generate.py --help` → exit code 0, shows all options
  - [ ] All modules import cleanly without errors
  - [ ] All expected files exist in project root
  - [ ] `git log --oneline` shows commits for all 11 previous tasks
  - [ ] `git push origin main` succeeds (or already up to date)
  - [ ] `git status` shows clean working tree (nothing uncommitted)

  **QA Scenarios**:

  ```
  Scenario: Full test suite passes
    Tool: Bash
    Preconditions: All test files from Tasks 2-10 exist
    Steps:
      1. Run `pytest tests/ -v` → capture output
      2. Assert exit code 0
      3. Assert output contains "passed" and "0 failed" (or no "FAILED" lines)
    Expected Result: All tests pass with zero failures
    Failure Indicators: Any test failure, import error, missing fixture
    Evidence: .sisyphus/evidence/task-12-tests.txt

  Scenario: Project structure complete
    Tool: Bash
    Preconditions: All tasks completed
    Steps:
      1. Verify all expected files exist:
         `ls generate.py pyproject.toml config.example.yaml README.md LICENSE .gitignore`
         `ls src/__init__.py src/browser.py src/flow.py src/downloader.py src/selectors.py src/config.py src/utils.py src/reporter.py`
         `ls tests/__init__.py tests/test_config.py tests/test_utils.py tests/test_batch.py`
      2. Assert all files found (exit code 0 for each ls)
    Expected Result: All project files present
    Failure Indicators: "No such file" error for any expected file
    Evidence: .sisyphus/evidence/task-12-structure.txt

  Scenario: Git repo clean and pushed
    Tool: Bash
    Preconditions: All commits made
    Steps:
      1. Run `git status` → assert "nothing to commit, working tree clean"
      2. Run `git log --oneline` → assert ≥12 commits (init + 11 task commits)
      3. Run `git remote -v` → assert contains "vaskoyudha/AutomationDownloadGoogleFlowImage"
    Expected Result: Clean repo with full commit history, correct remote
    Failure Indicators: Uncommitted changes, missing commits, wrong remote
    Evidence: .sisyphus/evidence/task-12-git.txt
  ```

  **Commit**: YES (if any final fixes needed)
  - Message: `chore: final integration verification and cleanup`
  - Files: any fixes discovered during verification
  - Pre-commit: `pytest tests/ -v`

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
>
> **Do NOT auto-proceed after verification. Wait for user's explicit approval before marking work complete.**

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in `.sisyphus/evidence/`. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `pytest tests/ -v` + type checks. Review all changed files for: `as any`, empty catches, `print()` in prod (should use logging), commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic variable names (data/result/item/temp).
  Output: `Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill)
  Start from clean state. Run `python generate.py --help` → verify help text. Run `python generate.py "test image of a blue circle" --count 1` → verify browser opens, navigates to Flow, enters prompt, generates, downloads, saves to correct directory with correct naming. Check logs exist. Run batch mode with 2-prompt test file. Save evidence to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual code. Verify 1:1 — everything in spec was built (no missing), nothing beyond spec was built (no creep). Check "Must NOT do" compliance: no API endpoints, no image post-processing, no prompt modification, no GUI. Detect cross-task contamination. Flag unaccounted changes.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

| Commit # | Message | Key Files | Pre-commit Check |
|----------|---------|-----------|-----------------|
| 1 | `init: project scaffolding with pyproject.toml and uv setup` | pyproject.toml, .gitignore, src/__init__.py, generate.py (skeleton) | `python -c "import src"` |
| 2 | `feat(config): add YAML config loading and CLI argument parsing` | src/config.py, config.example.yaml, tests/test_config.py | `pytest tests/test_config.py` |
| 3 | `feat(utils): add filename sanitization, logging, and retry utilities` | src/utils.py, tests/test_utils.py | `pytest tests/test_utils.py` |
| 4 | `feat(batch): add batch file parser for txt and json formats` | src/config.py (batch methods), tests/test_batch.py | `pytest tests/test_batch.py` |
| 5 | `feat(browser): add Chrome profile management and Playwright session` | src/browser.py | `pytest tests/ -v` |
| 6 | `feat(selectors): add UI selector abstraction layer for Google Flow` | src/selectors.py | `python -c "from src.selectors import FlowSelectors"` |
| 7 | `feat(flow): add Google Flow page interaction layer` | src/flow.py | `pytest tests/ -v` |
| 8 | `feat(download): add image detection, download, and organized save` | src/downloader.py | `pytest tests/ -v` |
| 9 | `feat(resilience): add CAPTCHA detection, consent handling, retry logic` | src/flow.py (updates), src/utils.py (updates) | `pytest tests/ -v` |
| 10 | `feat(report): add session summary and log file generation` | src/reporter.py, generate.py (integration) | `pytest tests/ -v` |
| 11 | `docs: add comprehensive README with setup guide and usage examples` | README.md | — |
| 12 | `feat: final integration wiring and end-to-end verification` | generate.py (final) | `python generate.py --help` |

---

## Success Criteria

### Verification Commands
```bash
# All tests pass
pytest tests/ -v                     # Expected: all PASSED, 0 failed

# CLI help works
python generate.py --help            # Expected: shows --prompt, --batch, --aspect-ratio, --count, --output-dir

# Config loads
python -c "from src.config import load_config; c = load_config('config.example.yaml'); print(c)"
                                     # Expected: prints config dict with output_dir, default_count, etc.

# Filename sanitization works
python -c "from src.utils import sanitize_prompt; print(sanitize_prompt('Hello World! 🌅 café'))"
                                     # Expected: hello-world-caf

# Batch parsing works
python -c "
from src.config import parse_batch_file
prompts = parse_batch_file('tests/fixtures/sample_prompts.txt')
assert len(prompts) >= 2
print(f'Parsed {len(prompts)} prompts')
"                                    # Expected: Parsed N prompts

# Single generation (requires Chrome + Google login)
python generate.py "a simple blue circle on white background" --count 1
                                     # Expected: output/a-simple-blue-circle-on-white-background/...001.png created
```

### Final Checklist
- [ ] All "Must Have" present and working
- [ ] All "Must NOT Have" absent from codebase
- [ ] All pytest tests pass
- [ ] README has complete setup guide
- [ ] Repo pushed to GitHub with clean commit history
- [ ] Output directory structure matches naming convention

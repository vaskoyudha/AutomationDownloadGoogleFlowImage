# Decisions

## [2026-03-20] Architecture Decisions
- Browser automation ONLY — no API
- Python + Playwright (vanilla, no stealth forks)
- uv for package management
- All selectors in src/selectors.py only
- TDD for all pure logic (config, utils, batch, sanitization)
- Chrome profile copy strategy for avoiding lock conflicts
- Single YAML config file, no env vars
- Standard logging module only (no loguru/structlog)
- output/{slug}/{slug}_{date}_{NNN}.png naming convention

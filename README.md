# AutomationDownloadGoogleFlowImage

A professional CLI tool for automated image generation and downloading from Google Flow (labs.google/flow).

![Python](https://img.shields.io/badge/python-3.10%2B-blue)

## Features

- 🤖 **Browser automation**: Uses Playwright to navigate Google Flow and handle complex interactions.
- 📁 **Organized saves**: Automatically saves images into prompt-specific folders with clean timestamps.
- ⚙️ **Full settings control**: Configure aspect ratios, counts, models, and more via CLI or YAML.
- 🔄 **Retry with backoff**: Intelligent retry logic for handling network flakiness or generation delays.
- ⚠️ **CAPTCHA detection**: Automatically detects and pauses for CAPTCHA solving to prevent account blocks.
- 📊 **Session reports**: Generates comprehensive summaries and JSON logs for every automation run.

## Quick Start

1. **Install uv**: If you haven't already, install the [uv package manager](https://github.com/astral-sh/uv).
2. **Clone and Setup**: Clone the repo and install dependencies.
3. **Prepare Profile**: Log into your Google account in a standard Chrome browser.
4. **Configure**: Copy `config.example.yaml` to `config.yaml` and set your Chrome profile path.
5. **Generate**: Run `.venv/bin/python generate.py --prompt "a cosmic jellyfish in deep space"`.

## Prerequisites

- **Python 3.10+**
- **Google Chrome browser** installed on your system.
- **Google account** with a Google AI Plus subscription (required for Imagen 4).
- **uv package manager** for fast dependency management.

## Installation

```bash
git clone git@github.com:vaskoyudha/AutomationDownloadGoogleFlowImage.git
cd AutomationDownloadGoogleFlowImage
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
playwright install chromium
```

Note: You can also install the project in editable mode using `uv pip install .`.

## Chrome Profile Setup

To bypass login screens and use your existing Google AI Plus session, the tool uses your local Chrome profile.

1. Open Google Chrome on your computer.
2. Log into the Google account that has the active subscription.
3. Navigate to [labs.google/flow](https://labs.google/flow) and accept any terms, conditions, or intro popups.
4. Close Chrome completely. This is crucial as the profile cannot be accessed while Chrome is running.
5. Your profile is typically located at `~/.config/google-chrome/Default` (Linux) or `~/Library/Application Support/Google/Chrome/Default` (macOS).

## Usage

### CLI Help
```bash
usage: generate.py [-h] [--prompt PROMPT] [--batch BATCH]
                   [--aspect-ratio ASPECT_RATIO] [--count COUNT]
                   [--model MODEL] [--output-dir OUTPUT_DIR] [--config CONFIG]
                   [--headless]

options:
  -h, --help            show this help message and exit
  --prompt PROMPT       Single prompt for image generation
  --batch BATCH         Path to file with prompts (one per line)
  --aspect-ratio ASPECT_RATIO
                        Aspect ratio (e.g., 16:9, 1:1)
  --count COUNT         Number of images to generate per prompt
  --model MODEL         Model to use for generation
  --output-dir OUTPUT_DIR
                        Output directory for generated images
  --config CONFIG       Path to YAML config file
  --headless            Run browser in headless mode
```

### Examples

**Single Prompt**
```bash
.venv/bin/python generate.py --prompt "a sunset over mountains"
```

**Custom Settings**
```bash
.venv/bin/python generate.py --prompt "abstract art" --count 4 --aspect-ratio 16:9
```

**Batch Processing**
```bash
.venv/bin/python generate.py --batch prompts.txt
```

**Custom Output Directory**
```bash
.venv/bin/python generate.py --prompt "cat" --output-dir ~/my-images
```

**Using a Specific Config**
```bash
.venv/bin/python generate.py --config my-config.yaml --prompt "landscape"
```

## Configuration

The tool uses `config.yaml` for default settings. All options can be overridden by CLI arguments.

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `output_dir` | string | `output` | Base directory for all generated images. |
| `default_count` | integer | `4` | Number of images to generate per prompt. |
| `aspect_ratio` | string | `1:1` | Image aspect ratio (e.g., 1:1, 16:9, 4:3). |
| `model` | string | `auto` | Generation model to select in the UI. |
| `delay_between_generations` | integer | `10` | Seconds to wait between subsequent prompts. |
| `typing_speed_min` | integer | `50` | Minimum typing speed (chars per second). |
| `typing_speed_max` | integer | `150` | Maximum typing speed (chars per second). |
| `click_delay_min` | integer | `200` | Minimum delay after clicks (ms). |
| `click_delay_max` | integer | `500` | Maximum delay after clicks (ms). |
| `generation_timeout` | integer | `120` | Max seconds to wait for generation to finish. |
| `max_retries` | integer | `3` | Number of times to retry a failed generation. |
| `quota_wait_time` | integer | `60` | Seconds to wait if a quota limit is hit. |

## Batch File Format

### Text Format (.txt)
A simple list of prompts, one per line. Lines starting with `#` are treated as comments.

```text
# Nature prompts
A majestic mountain at sunrise with golden light
An underwater coral reef scene with colorful fish

# Urban prompts
A futuristic city skyline at night with neon lights
```

### JSON Format (.json)
Allows fine-grained control for each prompt in the batch.

```json
[
  {"prompt": "A majestic mountain at sunrise", "count": 2, "aspect_ratio": "16:9"},
  {"prompt": "An underwater coral reef", "count": 4},
  {"prompt": "A futuristic city skyline", "aspect_ratio": "9:16", "model": "auto"}
]
```

## Output Structure

Images are organized into subdirectories named after the prompt's slug.

```text
output/
└── a-majestic-mountain-at-sunrise/
    ├── a-majestic-mountain-at-sunrise_2026-03-20_001.png
    ├── a-majestic-mountain-at-sunrise_2026-03-20_002.png
    └── session_report.json
```

## Troubleshooting

- **"Chrome not found"**: Ensure Google Chrome is installed. On Linux, you might need to install it via your package manager (e.g., `sudo apt install google-chrome-stable`).
- **"Profile not found"**: Check your `config.yaml` or CLI arguments for the correct path to your Chrome profile. Ensure you've followed the Profile Setup guide.
- **"CAPTCHA detected"**: The tool will pause execution and alert you. Switch to the browser window, solve the CAPTCHA manually, and the tool will resume.
- **"Safety filter rejected"**: Google Flow may reject certain prompts. Try rephrasing your prompt to be more descriptive or less ambiguous.
- **"Quota exceeded"**: You've hit Google's generation limits. The tool will wait for the configured `quota_wait_time` before retrying.
- **"Generation timeout"**: If images are taking too long to generate, increase the `generation_timeout` value in your `config.yaml`.

## How It Works

The tool is built with a modular architecture:
- `generate.py`: The main entry point handling CLI and batch flow.
- `src/browser.py`: Manages the Playwright browser instance and profile isolation.
- `src/flow.py`: Implements the page object pattern for interacting with the Google Flow UI.
- `src/downloader.py`: Handles complex image retrieval strategies (blob detection, canvas capture).
- `src/config.py`: Centralized configuration and argument parsing.
- `src/reporter.py`: Tracks session progress and generates final summaries.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

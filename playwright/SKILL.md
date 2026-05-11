---
name: playwright
description: "Browser automation via Playwright. Navigate, click, type, extract data, take screenshots, and assert page state. Use for E2E testing, scraping, and UI verification."
version: 0.1.0
---

# Playwright Skill

Browser automation agent skill. Drives headless Chromium via Playwright Python API.

## Usage

```bash
python main.py --url <URL> --action <action_type> [--selector <CSS>] [--value <text>] [--output <file>]
```

### Actions

| Action | Args | Description |
|---|---|---|
| `navigate` | `--url` | Open URL, wait for load |
| `click` | `--selector` | Click element |
| `type` | `--selector`, `--value` | Type into input |
| `extract` | `--selector` | Get text content |
| `screenshot` | `--output` | Save page screenshot |
| `wait` | `--selector`, `--timeout` | Wait for element |
| `eval` | `--value` | Execute JS, return result |
| `scroll` | `--value` | Scroll to (top/bottom/px) |

## Examples

```bash
# Navigate and screenshot
python main.py --url https://example.com --action navigate
python main.py --action screenshot --output page.png

# Click and extract
python main.py --action click --selector "#submit-btn"
python main.py --action extract --selector "h1"

# Type into form
python main.py --action type --selector "#search" --value "hello"

# Execute JS
python main.py --action eval --value "document.title"
```

## Session Mode

For multi-step flows, use session mode (stateful browser):

```bash
python main.py --session start --url https://example.com
python main.py --session interact --action click --selector "#btn"
python main.py --session screenshot --output result.png
python main.py --session stop
```

## Setup

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Output

- Text actions → stdout (JSON or plain text)
- Screenshots → file path
- Errors → stderr + exit code 1

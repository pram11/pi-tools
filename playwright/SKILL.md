---
name: playwright
description: "Browser automation via Playwright. Navigate, click, type, extract data, take screenshots, assert page state, scrape tables, intercept network, generate PDFs, handle shadow DOM/iframes/dialogs, upload files, manage auth, orchestrate multi-tab flows. Use for E2E testing, scraping, form automation, and UI verification."
version: 0.7.0
---

# Playwright Skill

Headless Chromium automation via Playwright Python API. 46 built-in actions across 7 capability tiers.

## Usage

> **Use project venv, not system Python. All deps live in `.venv/`.

```bash
.venv/bin/python main.py --url <URL> --action <ACTION> [--selector <CSS>] [--value <TEXT>] [--output <FILE>]
```

### Extra Flags

| Flag | Purpose |
|---|---|
| `--timeout <MS>` | Navigation timeout (default 30000) |
| `--retries <N>` | Auto-retry on crash/timeout (default 1) |
| `--baseline <FILE>` | Baseline screenshot for `screenshot-diff` |
| `--nth <N>` | 0-based index slice for `extract-all` |

## Actions

### Phase 1 — Core (8)

| Action | Args | Description |
|---|---|---|
| `navigate` | `--url` | Open URL, wait for domcontentloaded |
| `click` | `--selector` | Click element |
| `type` | `--selector`, `--value` | Fill input field |
| `extract` | `--selector` | Get text content |
| `screenshot` | `--output` | Save full-page screenshot |
| `wait` | `--selector`, `--value` (timeout ms) | Wait for element |
| `eval` | `--value` | Execute JS, return JSON |
| `scroll` | `--value` (top/bottom/px) | Scroll page |

### Phase 3 — Form Automation (4)

| Action | Args | Description |
|---|---|---|
| `form-detect` | — | List all form fields (name, type, required) |
| `smart-fill` | `--value` (JSON `{name: val}`) | Auto-fill fields by name |
| `submit` | `--selector` | Submit form, wait for navigation |
| `wizard` | `--value` (JSON steps array), `--selector` (next btn) | Multi-step wizard fill |

### Phase 4 — Data Extraction (4)

| Action | Args | Description |
|---|---|---|
| `scrape` | `--selector` (table), `--value` (json/csv) | Table rows → JSON/CSV |
| `extract-all` | `--selector` (parent), `--value` (child sel or JSON map), `--nth` | Repeated block extraction |
| `network` | `--url` | Capture all API responses + headers |
| `pdf` | `--output` | Generate PDF from current page |

### Phase 5 — Assertions & Testing (5)

| Action | Args | Description |
|---|---|---|
| `expect-text` | `--selector`, `--value` (expected) | Assert text contains string |
| `expect-visible` | `--selector` | Assert element visible |
| `expect-url` | `--value` (expected substring) | Assert URL contains string |
| `screenshot-diff` | `--baseline`, `--output`, `--value` (threshold) | Pixel diff + similarity score |
| `report` | `--value` (JSON specs array) | Batch assertions, JSON/text summary |

### Phase 6 — Advanced Patterns (21)

| Action | Args | Description |
|---|---|---|
| `shadow-detect` | — | List all shadow hosts |
| `shadow-query` | `--selector` (host), `--value` (inner) | Read text from shadow root |
| `shadow-click` | `--selector` (host), `--value` (inner) | Click inside shadow root |
| `shadow-fill` | `--selector` (host), `--value` (inner), `--output` (text) | Fill inside shadow root |
| `shadow-extract` | `--selector` (host), `--value` (inner) | Extract all matching inner texts |
| `shadow-pierce` | `--value` (`#host >> .deep >> .el`) | Multi-level shadow piercing |
| `iframe-list` | — | List all iframes + metadata |
| `iframe-query` | `--selector` (iframe), `--value` (inner) | Read text from iframe |
| `iframe-click` | `--selector` (iframe), `--value` (inner) | Click inside iframe |
| `iframe-fill` | `--selector` (iframe), `--value` (inner), `--output` (text) | Fill inside iframe |
| `iframe-extract` | `--selector` (iframe), `--value` (inner) | Extract text from iframe |
| `dialog-accept` | `--selector` (trigger) | Auto-accept all dialogs |
| `dialog-dismiss` | `--selector` (trigger) | Auto-dismiss all dialogs |
| `dialog-prompt` | `--selector` (trigger), `--value` (prompt text) | Accept prompt with text |
| `upload` | `--selector` (input), `--value` (path[,path]) | Upload file(s) |
| `upload-detect` | — | List all file input elements |
| `auth-inject` | `--url`, `--value` (JSON), `--output` (cookies/localStorage/headers) | Seed auth state |
| `auth-clear` | — | Clear cookies + localStorage |
| `tabs-open` | `--value` (count) | Open N new tabs |
| `tabs-list` | — | List all open tabs |
| `tabs-switch` | `--value` (index) | Switch to tab by 0-based index |
| `tabs-close` | `--value` (index) | Close specific tab |
| `tabs-close-all` | — | Close all tabs |
| `tabs-broadcast` | `--value` (JSON: `[{action, args}]`) | Run action on each tab |
| `tabs-gather` | `--value` (JS expr) | Evaluate JS on each tab, collect results |

## Session Mode (Stateful Browser)

Persistent context via `session-start` / `session-stop`. State stored in `.sessions/`.

```bash
# Start session (navigates + saves cookies/localStorage)
.venv/bin/python main.py session-start --url https://example.com

# Subsequent actions reuse storage state (cookies, localStorage)
.venv/bin/python main.py --action click --selector "#btn"
.venv/bin/python main.py --action extract --selector "h1"
.venv/bin/python main.py --action screenshot --output result.png

# End session (clears state)
.venv/bin/python main.py session-stop
```

## Examples

```bash
# Navigate + screenshot
.venv/bin/python main.py --url https://example.com --action navigate
.venv/bin/python main.py --action screenshot --output page.png

# Click + extract
.venv/bin/python main.py --action click --selector "#submit"
.venv/bin/python main.py --action extract --selector "h1"

# JS evaluation
.venv/bin/python main.py --action eval --value "document.title"

# Smart-fill form
.venv/bin/python main.py --action smart-fill --value '{"username":"admin","password":"s3cret"}'
.venv/bin/python main.py --action submit

# Scrape table to CSV
.venv/bin/python main.py --action scrape --selector "table" --value csv

# Multi-step wizard
.venv/bin/python main.py --action wizard --value '[{"fields":{"name":"A"},"next":".next"},{"fields":{"email":"a@b.com"},"submit":true}]'

# Shadow DOM pierce
.venv/bin/python main.py --action shadow-pierce --value "#app >> .modal >> .title"

# Network capture
.venv/bin/python main.py --url https://api.example.com --action network

# Auth injection (cookies)
.venv/bin/python main.py --url https://app.com --action auth-inject \
  --output cookies --value '[{"name":"token","value":"abc123"}]'

# Auth injection (localStorage)
.venv/bin/python main.py --url https://app.com --action auth-inject \
  --output localStorage --value '{"theme":"dark","lang":"en"}'

# Screenshot diff
.venv/bin/python main.py --action screenshot-diff --baseline expected.png --output actual.png --value 0.95

# Batch assertions
.venv/bin/python main.py --action report \
  --value '[{"type":"expect-text","selector":"h1","value":"Hello"},{"type":"expect-visible","selector":"#logo","value":""}]'

# Multi-tab orchestration
.venv/bin/python main.py --action tabs-open --value 3
.venv/bin/python main.py --action tabs-gather --value "document.title"
.venv/bin/python main.py --action tabs-broadcast --value '[{"action":"goto","args":["https://a.com"]},{"action":"goto","args":["https://b.com"]},{"action":"goto","args":["https://c.com"]}]'

# Dialog handling
.venv/bin/python main.py --action dialog-accept --selector "#confirm-btn"
.venv/bin/python main.py --action dialog-prompt --selector "#prompt-btn" --value "my answer"
```

## Setup

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
```

## Output

- Text/JSON actions → stdout
- Screenshots / PDFs → file path on stdout
- Errors → stderr + exit code 1

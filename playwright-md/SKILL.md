---
name: playwright-md
description: "URL to Markdown via Playwright + html2md chain. Navigate any page (including JS-rendered), extract HTML, convert to clean Markdown. Supports auth injection, wait conditions, sub-region extraction, and batch URLs."
version: 0.1.0
---

# playwright-md Skill

Single-command URL→Markdown. Chains Playwright (headless browser) with html2md (converter). One CLI call replaces two-step manual piping.

## Usage

> **Use project venv, not system Python.** All deps live in `.venv/`.

```bash
.venv/bin/python main.py --url <URL> --action page-to-md
```

### Arguments

| Flag | Type | Default | Description |
|---|---|---|---|
| `--url` | string | — | Target URL |
| `--urls` | file | — | File with one URL per line (batch mode) |
| `--action` | `page-to-md` | `page-to-md` | Action to perform |
| `--output` | path | stdout | Write Markdown to file |
| `--output-dir` | path | — | Output directory (batch mode) |
| `--wait-for` | selector | — | Wait for CSS selector before extraction |
| `--wait-for-url` | pattern | — | Wait for URL to match substring |
| `--timeout` | int | 30000 | Navigation timeout (ms) |
| `--retries` | int | 1 | Auto-retry on crash/timeout |
| `--selector` | CSS | — | Extract sub-region HTML (not full page) |
| `--backend` | `markdownify` \| `html2text` | `markdownify` | html2md converter backend |
| `--cookies` | JSON string | — | Inject cookies array `[{"name":"x","value":"y"}]` |
| `--headers` | JSON string | — | Inject custom headers `{"User-Agent":"bot"}` |
| `--version` | — | — | Print version and exit |
| `--session-dir` | path | `<skill-root>/.sessions` | Persistent browser state directory (saves/reads `storage_state.json`) |

## Actions

| Action | Description |
|---|---|
| `page-to-md` | Navigate URL → wait → extract HTML → convert → Markdown output |

## Pipeline

```
URL → Playwright navigate (chromium headless) → wait conditions → extract HTML
  → sanitize (strip script/style/noscript/link/meta, strip images)
  → html2md convert → post-process (collapse blanks, strip trailing ws) → Markdown
```

**Note:** Image stripping is hardcoded in both backends. No CLI flag to re-enable.

## Examples

### Basic URL to Markdown
```bash
.venv/bin/python main.py --url https://example.com --action page-to-md
```

### Save to file
```bash
.venv/bin/python main.py --url https://example.com --action page-to-md --output page.md
```

### Wait for dynamic content
```bash
.venv/bin/python main.py --url https://app.com/dashboard \
  --action page-to-md \
  --wait-for "#data-table" --timeout 15000
```

### Auth via cookies
```bash
.venv/bin/python main.py --url https://app.com \
  --action page-to-md \
  --cookies '[{"name":"session","value":"abc123","domain":".app.com"}]'
```

### Sub-region extraction
```bash
.venv/bin/python main.py --url https://docs.example.com \
  --action page-to-md \
  --selector "main article"
```

### Batch mode
```bash
.venv/bin/python main.py --urls urls.txt --output-dir ./output/
```

URL file supports `#` comment lines and blank lines (skipped). Filenames auto-generated from URLs. Progress + summary → stderr.

### Switch backend
```bash
.venv/bin/python main.py --url https://example.com \
  --action page-to-md --backend html2text
```

## Dependencies

| Dependency | Type | Role |
|---|---|---|
| `playwright` | pip package | Browser automation (navigate, extract HTML) |
| `html2md` | sibling skill (`../html2md/`) | HTML → Markdown conversion |
| `beautifulsoup4` | pip package | HTML parsing/sanitization |
| `markdownify` / `html2text` | pip packages | Conversion backends |

`../html2md/` path injected at runtime via `SkillPathResolver`.

## Setup

```bash
.venv/bin/pip install -r requirements.txt
.venv/bin/python -m playwright install chromium
```

## Auth / Session State

`--session-dir` persists browser state to `<dir>/storage_state.json`.
Next run auto-loads saved state → preserves cookies/localStorage.
Pair with `--cookies` or `--headers` for initial auth injection.

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Success |
| `1` | Failure (navigation, retry exhausted, bad args) |
| `130` | KeyboardInterrupt (Ctrl+C) |

---
name: playwright-md
description: "URL to Markdown via Playwright + html2md chain. Navigate any page (including JS-rendered), extract HTML, convert to clean Markdown. Supports auth injection, wait conditions, sub-region extraction, and batch URLs."
version: 0.2.0
---

# playwright-md Skill

Single-command URL→Markdown. Chains Playwright (headless browser) with html2md (converter). One CLI call replaces two-step manual piping.

## Usage

> **Use project venv, not system Python.** All deps live in `.venv/`.

### ⚠️ Token Efficiency: Always Prefer `--core-only`

Full-page extraction includes nav, footer, ads, sidebar → massive token waste. **Default to `--core-only`** unless full page is explicitly required.

```bash
# ✅ Preferred: core content only (strips nav/header/footer/aside/ads)
.venv/bin/python main.py --url <URL> --action page-to-md --core-only

# ❌ Avoid: full page (noisy, token-heavy)
.venv/bin/python main.py --url <URL> --action page-to-md
```

When `--core-only` auto-detection is insufficient, use `--core-selector` with an explicit CSS target:

```bash
.venv/bin/python main.py --url <URL> --action page-to-md --core-selector "#main-content"
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
| `--core-only` | flag | false | Extract only core content (strip nav/header/footer/aside/ads) |
| `--core-selector` | CSS | — | Explicit CSS selector for core content (overrides auto-detection) |

## Actions

| Action | Description |
|---|---|
| `page-to-md` | Navigate URL → wait → extract HTML → convert → Markdown output |

## Pipeline

```
URL → Playwright navigate (chromium headless) → wait conditions → extract HTML
  → sanitize (strip script/style/noscript/link/meta, strip images)
  → core extraction (optional, --core-only: strip nav/header/footer/aside/ads)
  → html2md convert → post-process (collapse blanks, strip trailing ws) → Markdown
```

**Note:** Image stripping is hardcoded in both backends. No CLI flag to re-enable.

## Examples

### Basic URL to Markdown
```bash
.venv/bin/python main.py --url https://example.com --action page-to-md --core-only
```

### Save to file
```bash
.venv/bin/python main.py --url https://example.com --action page-to-md --core-only --output page.md
```

### Wait for dynamic content
```bash
.venv/bin/python main.py --url https://app.com/dashboard \
  --action page-to-md \
  --core-only \
  --wait-for "#data-table" --timeout 15000
```

### Auth via cookies
```bash
.venv/bin/python main.py --url https://app.com \
  --action page-to-md \
  --core-only \
  --cookies '[{"name":"session","value":"abc123","domain":".app.com"}]'
```

### Sub-region extraction (alternative to --core-only)
```bash
.venv/bin/python main.py --url https://docs.example.com \
  --action page-to-md \
  --selector "main article"
```

### Batch mode (core-only default)
```bash
.venv/bin/python main.py --urls urls.txt --output-dir ./output/ --core-only
```

URL file supports `#` comment lines and blank lines (skipped). Filenames auto-generated from URLs. Progress + summary → stderr.

### Switch backend
```bash
.venv/bin/python main.py --url https://example.com \
  --action page-to-md --backend html2text
```

### Core content only (strip nav/footer/ads)
```bash
.venv/bin/python main.py --url https://news.example.com/article \
  --action page-to-md --core-only
```

### Core with explicit selector
```bash
.venv/bin/python main.py --url https://example.com \
  --action page-to-md --core-selector "#article-body"
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

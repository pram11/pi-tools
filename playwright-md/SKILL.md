---
name: playwright-md
description: "URL to Markdown via Playwright + html2md chain. Navigate any page (including JS-rendered), extract HTML, convert to clean Markdown. Supports auth injection, wait conditions, sub-region extraction, and batch URLs."
version: 0.3.0
---

# playwright-md Skill

Single-command URL→Markdown. Single Rust binary chains Playwright (headless browser) with comrak (converter). One CLI call replaces two-step manual piping.

## Usage

### ⚠️ Token Efficiency: Always Prefer `--core-only`

Full-page extraction includes nav, footer, ads, sidebar → massive token waste. **Default to `--core-only`** unless full page is explicitly required.

```bash
# ✅ Preferred: core content only (strips nav/header/footer/aside/ads)
./target/release/playwright-md --url <URL> --action page-to-md --core-only

# ❌ Avoid: full page (noisy, token-heavy)
./target/release/playwright-md --url <URL> --action page-to-md
```

When `--core-only` auto-detection is insufficient, use `--core-selector` with an explicit CSS target:

```bash
./target/release/playwright-md --url <URL> --action page-to-md --core-selector "#main-content"
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
| `--pre-action` | string | — | Semicolon-separated actions delegated to `../playwright/` (e.g. `click,#btn;type,#search,qwerty`) |
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
  → pre-actions (optional, --pre-action: delegate to ../playwright/)
  → sanitize (strip script/style/noscript/link/meta, strip images)
  → core extraction (optional, --core-only: strip nav/header/footer/aside/ads)
  → comrak convert → post-process (collapse blanks, strip trailing ws) → Markdown
```

**Note:** Image stripping is hardcoded. No CLI flag to re-enable.

## Examples

### Basic URL to Markdown
```bash
./target/release/playwright-md --url https://example.com --action page-to-md --core-only
```

### Save to file
```bash
./target/release/playwright-md --url https://example.com --action page-to-md --core-only --output page.md
```

### Wait for dynamic content
```bash
./target/release/playwright-md --url https://app.com/dashboard \
  --action page-to-md \
  --core-only \
  --wait-for "#data-table" --timeout 15000
```

### Auth via cookies
```bash
./target/release/playwright-md --url https://app.com \
  --action page-to-md \
  --core-only \
  --cookies '[{"name":"session","value":"abc123","domain":".app.com"}]'
```

### Sub-region extraction (alternative to --core-only)
```bash
./target/release/playwright-md --url https://docs.example.com \
  --action page-to-md \
  --selector "main article"
```

### Batch mode (core-only default)
```bash
./target/release/playwright-md --urls urls.txt --output-dir ./output/ --core-only
```

URL file supports `#` comment lines and blank lines (skipped). Filenames auto-generated from URLs. Progress + summary → stderr.

### Core content only (strip nav/footer/ads)
```bash
./target/release/playwright-md --url https://news.example.com/article \
  --action page-to-md --core-only
```

### Core with explicit selector
```bash
./target/release/playwright-md --url https://example.com \
  --action page-to-md --core-selector "#article-body"
```

### Pre-action chain via ../playwright/
```bash
./target/release/playwright-md --url https://app.com \
  --action page-to-md \
  --core-only \
  --pre-action "click,#login;type,#user,admin;type,#pass,s3cret;click,#submit;wait,#dashboard"
```

## Dependencies

| Dependency | Type | Role |
|---|---|---|
| `playwright` | Rust crate | Browser automation (navigate, extract HTML) |
| `comrak` | Rust crate | HTML → Markdown conversion |
| `ammonia` | Rust crate | HTML parsing/sanitization |
| `clap` | Rust crate | CLI argument parsing |
| `tokio` | Rust crate | Async runtime |
| `tracing` | Rust crate | Logging/telemetry |
| `thiserror` | Rust crate | Error handling |

### Sibling Skill Chain

**`../playwright/`** — relative path to sibling playwright skill. Pre-actions (`--pre-action`) are delegated here for complex browser interactions (click, type, shadow DOM, iframes, upload, dialog handling, multi-tab). Core pipeline (navigate → extract → convert) stays in-process.

```bash
# Click, type, wait — then extract as Markdown
./target/release/playwright-md --url https://app.com \
  --action page-to-md \
  --core-only \
  --pre-action "click,#search-btn;type,#input,hello;wait,#results"
```

Pre-actions support all `../playwright/` actions: `click`, `type`, `wait`, `scroll`, `eval`, `dialog-*`, `shadow-*`, `iframe-*`, `upload`.

## Setup

```bash
cargo build --release
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

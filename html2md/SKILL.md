---
name: html2md
description: "Converts HTML to clean Markdown. Supports file input, inline string, and stdin. Two pluggable backends. No network — pure local conversion."
version: 0.2.0
---

# html2md Skill

Convert HTML documents to Markdown for LLM context, documentation, or storage.

**Rust (active)** + **Python (legacy)**. Both share CLI interface.

## Usage — Rust (default)

```bash
cargo run -- --file <path.html>
cargo run -- --html "<div>Hello</div>"
echo "<h1>hi</h1>" | cargo run
```

## Usage — Python (legacy)

```bash
.venv/bin/python main.py --file <path.html>
.venv/bin/python main.py --html "<div>Hello</div>"
echo "<h1>hi</h1>" | .venv/bin/python main.py
```

### Arguments

| Flag | Type | Default | Description |
|---|---|---|---|
| `--file` | path | — | Local HTML file to convert |
| `--html` | string | — | Inline HTML string |
| `--output` | path | stdout | Write Markdown to file instead of stdout |
| `--backend` | backend name | primary | Converter backend |
| `--wrap` | int | `0` | Line wrap width (0 = no wrap) |
| `--strip-images` | flag | false | Omit `<img>` tags from output |
| `--strip-links` | flag | false | Omit `<a>` tags, keep text only |

### Backends

| Impl | Primary | Fallback |
|---|---|---|
| Rust | `comrak` — full GFM (tables, lists, code, blockquotes) | `custom` — simplified html2text-style |
| Python | `markdownify` — GFM, tables, clean lists | `html2text` — aggressive simplification |

## Input Priority

`--file` → `--html` → stdin (piped input). If none provided → error.

## Examples

### Convert local HTML file
```bash
cargo run -- --file page.html
```

### Convert to file
```bash
cargo run -- --file page.html --output notes.md
```

### Inline HTML string
```bash
cargo run -- --html "<ul><li>A</li><li>B</li></ul>"
```

### Switch backend
```bash
cargo run -- --file page.html --backend custom
```

### Strip images, wrap at 80 chars
```bash
cargo run -- --file page.html --strip-images --wrap 80
```

### Pipe from Playwright (external skill chain)
```bash
# Step 1: playwright skill extracts raw HTML
.venv/bin/python playwright/main.py --url https://example.com --action eval --value "document.documentElement.outerHTML"

# Step 2: pipe into html2md
.venv/bin/python playwright/main.py --url https://example.com --action eval --value "..." | cargo run
```

## Pipeline

```
HTML input → sanitize (strip script/style/noscript)
         → converter (backend strategy)
         → post-processor (dedup blanks, normalize)
         → Markdown output
```

## Setup

```bash
# Rust (default)
cargo build

# Python (legacy)
.venv/bin/pip install -r requirements.txt
```

## Testing

```bash
# Rust — 49 tests (47 unit/e2e + 2 doc)
cargo test

# Python (legacy)
pytest tests/
```

---
name: html2md
description: "Converts HTML to clean Markdown. Supports file input, inline string, and stdin. Two pluggable backends (markdownify, html2text). No network — pure local conversion."
version: 0.1.0
---

# html2md Skill

Convert HTML documents to Markdown for LLM context, documentation, or storage.

## Usage

> **Use project venv, not system Python. All deps live in `.venv/`.

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
| `--backend` | `markdownify` \| `html2text` | `markdownify` | Converter backend |
| `--wrap` | int | — | Line wrap width (0 = no wrap) |
| `--strip-images` | flag | false | Omit `<img>` tags from output |
| `--strip-links` | flag | false | Omit `<a>` tags, keep text only |

## Input Priority

`--file` → `--html` → stdin (piped input). If none provided → error.

## Backends

| Backend | Library | Strengths |
|---|---|---|
| `markdownify` (default) | `markdownify` | GFM support, table handling, clean list formatting |
| `html2text` (fallback) | `html2text` | Aggressive simplification, bold/italic via Markdown syntax |

## Examples

### Convert local HTML file
```bash
.venv/bin/python main.py --file page.html
```

### Convert to file
```bash
.venv/bin/python main.py --file page.html --output notes.md
```

### Inline HTML string
```bash
.venv/bin/python main.py --html "<ul><li>A</li><li>B</li></ul>"
```

### Switch backend
```bash
.venv/bin/python main.py --file page.html --backend html2text
```

### Strip images, wrap at 80 chars
```bash
.venv/bin/python main.py --file page.html --strip-images --wrap 80
```

### Pipe from Playwright (external skill chain)
```bash
# Step 1: playwright skill extracts raw HTML
.venv/bin/python playwright/main.py --url https://example.com --action eval --value "document.documentElement.outerHTML"

# Step 2: pipe into html2md
.venv/bin/python playwright/main.py --url https://example.com --action eval --value "..." | .venv/bin/python html2md/main.py
```

## Pipeline

```
HTML input → html_parser (sanitize, strip script/style)
         → md_converter (backend strategy)
         → post_processor (dedup blanks, normalize lists)
         → Markdown output
```

## Setup

```bash
.venv/bin/pip install -r requirements.txt
```

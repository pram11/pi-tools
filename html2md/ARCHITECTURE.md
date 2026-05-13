# html2md — Architecture

## Overview

Pure HTML → Markdown converter. No network. No URL fetching. Two pluggable backends. Deterministic output.

## Pipeline

```
raw HTML → sanitize → converter (strategy) → post-process → Markdown
```

## Module Map (Rust — active)

```
src/
├── main.rs              # CLI entry (clap). Input priority: --file > --html > stdin
├── converter.rs         # trait Converter { name(), convert() }
├── sanitizer.rs         # ammonia: strip script/style/noscript
├── engine.rs            # strategy registry + dispatch + post-processing
├── post_processor.rs    # dedup blanks, rstrip, trim
└── backend/
    ├── mod.rs
    ├── comrak.rs        # Backend A: scraper DOM → full GFM
    └── custom.rs        # Backend B: scraper DOM → simplified MD
```

## Module Map (Python — legacy)

```
main.py                   # CLI entry (argparse)
base.py                   # abstract BaseConverter
lib/html_parser.py        # BeautifulSoup parse + sanitize
lib/md_converter.py       # strategy dispatcher + post-processing
lib/post_processor.py     # cleanup regex
plugins/markdownify_backend.py   # Backend A
plugins/html2text_backend.py     # Backend B
```

## Strategy Pattern

```
Converter (trait / ABC)
├── comrak / markdownify  — primary, fast, spec-compliant
└── custom / html2text    — fallback, different output flavor
```

Engine holds a registry (`OnceLock<HashMap<&str, &dyn Converter>>`). Lookup by name. Unknown → error.

- Both Rust backends share `scraper` + `ammonia` (no external HTML→MD crate).
- Python backends use `markdownify` / `html2text` libraries.

## Error Flow

All public APIs return `Result<T, Html2MdError>`. CLI catches, prints to stderr, exits code 1. Agent can retry with alternate backend.

## Input Priority

1. `--file <path>` — read local HTML file
2. `--html "<string>"` — inline HTML string
3. stdin — piped input (only if not a tty)
4. none → error + usage message

## Output

- stdout by default
- `--output <file>` redirects to file
- `--wrap <N>` line wrapping (0 = no wrap)
- `--strip-images` omit `<img>` tags
- `--strip-links` omit `<a>` tags

## Integration

Playwright skill chains externally: `page.content()` → pipe to html2md binary/stdin.

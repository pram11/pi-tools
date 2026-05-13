# Architecture — playwright-md (Rust Port)

## Overview
Single-binary CLI. Rust rewrite of Python `playwright-md`. Same linear pipeline, zero external process forks.

## Stack
- **Language**: Rust (stable toolchain)
- **Browser Automation**: `playwright` crate (official Rust bindings via `playwright`)
- **HTML Sanitization**: `ammonia` crate
- **HTML → Markdown**: `comrak` crate (CommonMark + GFM)
- **CLI Parsing**: `clap` (derive API)
- **Async Runtime**: `tokio` (multi-threaded, single-threaded profile optional)
- **Logging**: `tracing` + `tracing-subscriber` (stderr, JSON optional)

## Module Layout
```
src/
├── main.rs            # entry, CLI wiring, async runtime bootstrap
├── cli.rs             # clap structs, argument validation
├── pipeline.rs        # orchestrate: navigate → wait → extract → sanitize → convert → output
├── browser.rs         # playwright browser/lifecycle management
├── sanitize.rs        # strip <script>/<style>/<noscript> via ammonia
├── convert.rs         # html → md via comrak
├── output.rs          # stdout vs file sink
├── config.rs          # defaults, env overrides
└── errors.rs          # thiserror chain, context wrappers
```

## Pipeline
```
CLI args → clap validation
  → tokio::runtime::new().block_on(pipeline(args))
    → browser::launch()
    → browser::navigate(url)
    → browser::wait_for(condition?)
    → page::content() → raw HTML
    → sanitize::strip(raw) → clean HTML
    → convert::to_markdown(clean) → md string
    → output::write(md, dest?)
    → browser::close() (in Drop/finally)
```

## Sibling Skill Chain

**`../playwright/`** — relative path to sibling playwright skill. Used for pre-action browser automation before HTML extraction.

```
playwright-md --pre-action "click,#btn;type,#search,qwerty;wait,#results"
  → spawns ../playwright/main.py (or binary) for each pre-action step
  → returns to playwright-md pipeline for extract → sanitize → convert
```

Pre-actions support: `click`, `type`, `wait`, `scroll`, `eval`, `dialog-accept`, `shadow-*`, `iframe-*`, `upload`.

## Key Decisions
- **Subprocess for pre-actions only** — `../playwright/` spawned for complex interactions. Core pipeline (navigate → extract → convert) stays in-process.
- **Direct crate imports for core** — browser launch, HTML extraction, sanitize, convert all inline.
- **Ownership over borrowing** — HTML strings passed by value through pipeline; no shared state.
- **Graceful shutdown** — `browser::close()` in `Drop` impl + explicit `await` in finally-equivalent block.
- **Error propagation** — `thiserror` + `?` operator; every stage returns `Result<T, AppError>`.
- **Cookie/Auth injection** — `playwright` crate `context.add_cookies()` before navigation.
- **Selector extraction** — optional `core-selector` → query `page.query_selector()` → `element.inner_html()` instead of full page.

## Build & Run
```bash
# Build
cargo build --release

# Run
./target/release/playwright-md --url <URL> --action page-to-md
```

## Testing
- `cargo test` — unit tests per module
- `cargo test -- --test-threads=1` — integration tests requiring browser
- Snapshot tests for html2md output determinism

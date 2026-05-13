# Plan — playwright-md Rust Port

## Phase 1: Scaffold
- [ ] Initialize Cargo project (`cargo init`)
- [ ] Add dependencies: `playwright`, `comrak`, `ammonia`, `clap`, `tokio`, `tracing`, `thiserror`
- [ ] Module skeleton (`src/cli.rs`, `src/pipeline.rs`, `src/browser.rs`, `src/sanitize.rs`, `src/convert.rs`, `src/output.rs`, `src/errors.rs`)
- [ ] Basic `main.rs` → parse args → print hello

## Phase 2: Browser Layer
- [ ] `browser::launch()` — headless Chromium via playwright crate
- [ ] `browser::navigate(url)` — with timeout
- [ ] `browser::close()` — Drop impl + explicit close
- [ ] Cookie injection: `context.add_cookies()`

## Phase 3: Pipeline Core
- [ ] `pipeline::run(args)` — wire navigate → extract → sanitize → convert → output
- [ ] HTML extraction: `page.content()` / `page.query_selector()` for core-selector
- [ ] Sanitize: `ammonia::clean()` — strip script/style/noscript
- [ ] Convert: `comrak::markdown_to_html` (reversed) / `comrak::html_to_md` equivalent
- [ ] Wait conditions: `--wait-for` (selector), `--wait-for-url` (navigation)

## Phase 4: CLI Parity
- [ ] All original args: `--url`, `--action`, `--output`, `--cookies`, `--core-only`, `--core-selector`, `--wait-for`, `--wait-for-url`, `--retries`
- [ ] Stdout default, `--output` → file
- [ ] Exit codes: 0 success, 1 error
- [ ] Stderr logging via tracing

## Phase 4b: Sibling Skill Chain (`../playwright/`)
- [ ] `--pre-action` flag: semicolon-separated action list
- [ ] Subprocess launcher: resolve `../playwright/` relative to skill root → invoke per action step
- [ ] Action parser: split `action,sel,val` tuples → map to playwright CLI args
- [ ] Supported actions: `click`, `type`, `wait`, `scroll`, `eval`, `dialog-*`, `shadow-*`, `iframe-*`, `upload`
- [ ] Error propagation: playwright subprocess failure → abort pipeline, exit 1
- [ ] State handoff: share session/context between pre-actions (same `--session-dir`)
- [ ] Integration test: `click` + `type` + `wait` → verify DOM mutation before extract

## Phase 5: Polish
- [ ] Unit tests per module
- [ ] Integration tests (browser required)
- [ ] `cargo clippy` clean
- [ ] Benchmark vs Python version (cold start, throughput)
- [ ] Binary distribution (static linking? musl?)

## Phase 6: Cutover
- [ ] Feature parity verified against Python version
- [ ] Update skill definition
- [ ] Archive Python source (optional)
- [ ] Deploy

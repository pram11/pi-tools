# Implementation Plan: html2md Skill

## Phase 1: Core Scaffolding ✅
- [x] Establish `html2md/` directory structure.
- [x] Implement `main.py` CLI entry point (argparse dispatcher).
- [x] Define `BaseConverter` abstract class in `base.py`.
- [x] Write `SKILL.md`, `AGENTS.md`, `PLAN.md`.

## Phase 2: Conversion Pipeline ✅
- [x] Implement `lib/html_parser.py` — HTML sanitization + BeautifulSoup tree construction.
- [x] Implement `lib/md_converter.py` — core conversion engine with strategy pattern.
- [x] Implement `plugins/markdownify_backend.py` — primary converter (markdownify lib).
- [x] Implement `plugins/html2text_backend.py` — fallback converter (html2text lib).

## Phase 3: Post-Processing & Output ✅
- [x] Implement `lib/post_processor.py` — cleanup: dedup blanks, strip trailing spaces, normalize lists.
- [x] Support `--output <file>` flag for file destination.
- [x] Support `--wrap <N>` for line wrapping.

## Phase 4: Input Modes ✅
- [x] `--file <path>` — local HTML file input.
- [x] `--html "<string>"` — inline HTML string input.
- [x] stdin pipe — `echo "<h1>hi</h1>" | python main.py`.

## Phase 5: Testing & Integration
- [ ] Unit tests for each backend (markdownify, html2text).
- [ ] End-to-end tests: raw HTML → expected Markdown output.
- [ ] Register in `.pi/skills/html2md/` skill directory.
- [ ] Verify agent can invoke skill via terminal commands.

---

## Rust Port (TDD: Red → Green → Refactor)

### Crate Stack
| Crate | Purpose |
|-------|--------|
| `clap` v4 | CLI arg parsing |
| `html5ever` | HTML5 parsing |
| `scraper` | DOM traversal |
| `ammonia` | HTML sanitization |
| `comrak` | Backend A (HTML→MD) |
| `thiserror` | Error types |
| `tempfile` | E2E test fixtures |

### Phase R0: Scaffold ✅
- [x] `cargo init` + Cargo.toml deps
- [x] `cargo test` — empty, passes

### Phase R1: Sanitizer ✅
- [x] **RED** — `tests/test_sanitizer.rs`: script/style/noscript stripped (7 tests)
- [x] **GREEN** — `src/sanitizer.rs`: ammonia sanitize + serialize
- [x] **REFACTOR** — doc examples, unit test inline

### Phase R2: Converter Trait ✅
- [x] **RED** — `tests/test_converter.rs`: trait contract (name, convert) (7 tests)
- [x] **GREEN** — `src/converter.rs`: trait + error enum + Result type
- [x] **REFACTOR** — impl Debug on trait

### Phase R3: Post-Processor ✅
- [x] **RED** — `tests/test_post_processor.rs`: dedup blanks, rstrip, trim (7 tests)
- [x] **GREEN** — `src/post_processor.rs`: loop-based blank collapse
- [x] **REFACTOR** — doc example

### Phase R4: Backend A — comrak ✅
- [x] **GREEN** — `src/backend/comrak.rs`: scraper DOM → full MD (headings, paragraphs, links, lists, tables, code, blockquotes, hr, img)
- [x] Tests covered by `test_engine.rs` + `test_e2e.rs`

### Phase R5: Backend B — custom AST walker ✅
- [x] **GREEN** — `src/backend/custom.rs`: scraper DOM → simplified MD
- [x] Tests covered by `test_engine.rs` + `test_e2e.rs`

### Phase R6: Engine (Strategy Dispatcher) ✅
- [x] **RED** — `tests/test_engine.rs`: registry lookup, dispatch, unknown backend (10 tests)
- [x] **GREEN** — `src/engine.rs`: OnceLock registry, `get_backend()`, `convert()`

### Phase R7: CLI ✅
- [x] **RED** — `tests/test_e2e.rs`: no-args exit 1, --html, --file, not-found, --backend, --output, stdin, --wrap, --strip-images, --strip-links (13 tests)
- [x] **GREEN** — `src/main.rs`: clap args, input priority (file > html > stdin), dispatch, output

### Phase R8: Polish ✅
- [x] `cargo clippy -- -D warnings` — clean
- [x] `cargo fmt`
- [x] 47 tests, 0 failures, 2 doc-tests

**Total**: 47 unit/integration tests + 2 doc tests = **49 passing**

## Future (Out of Scope — Chained Skills)
- [ ] URL mode via Playwright skill → pipe `page.content()` into html2md.

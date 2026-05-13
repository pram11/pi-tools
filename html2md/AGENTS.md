# Pi html2md

This file defines coding standards, command protocols, and autonomous behavior for the html2md skill.

## Architecture
See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for full module map and pipeline.

- Single-process CLI dispatching to strategy-pattern converters.
- Two backends: primary (`comrak`/`markdownify`), fallback (`custom`/`html2text`).
- Pipeline: `raw HTML → sanitize → converter → post-processor → Markdown`.

## Plan
See [`PLAN.md`](./PLAN.md) for roadmap and milestones.

## Project Scope
- **Focus**: Pure HTML → Markdown conversion. No network, no URL fetching.
- **Goal**: Deterministic, agent-runnable converter with pluggable backends.
- **Integration**: Playwright skill chains externally (`page.content()` → pipe to this skill).

## Languages
- **Rust** (active) — `src/`, `Cargo.toml`, TDD via `cargo test`
- **Python** (legacy) — `main.py`, `lib/`, `plugins/`, maintained for compatibility

## Core Commands — Rust
- **Setup**: `cargo build`
- **Run**: `cargo run -- --file <path.html>`
- **From string**: `cargo run -- --html "<div>content</div>"`
- **Stdin**: `echo "<h1>hi</h1>" | cargo run`
- **To file**: `cargo run -- --file page.html --output result.md`
- **Switch backend**: `cargo run -- --file page.html --backend custom`
- **Tests (TDD)**: `cargo test` / `cargo test -- --nocapture`
- **Lint**: `cargo clippy -- -D warnings`
- **Format**: `cargo fmt`

## Core Commands — Python (legacy)
- **Setup**: `pip install -r requirements.txt`
- **From file**: `python main.py --file <path.html>`
- **From string**: `python main.py --html "<div>content</div>"`
- **Stdin**: `echo "<h1>hi</h1>" | python main.py`
- **To file**: `python main.py --file page.html --output result.md`
- **Switch backend**: `python main.py --file page.html --backend html2text`
- **Tests**: `pytest tests/`

## Behavior & Workflow
1. **Input Priority**: `--file` > `--html` > stdin. If none provided → error + usage.
2. **Backend Selection**: Default primary backend. Fallback to alternate on failure or explicit `--backend` flag.
3. **Sanitize First**: Always run HTML through sanitizer before conversion. Strips script/style/noscript tags.
4. **Error Handling**: All public APIs return `Result`. CLI logs to stderr, exit code 1 on failure. Agent can retry with alternate backend.
5. **Output**: Markdown to stdout by default. `--output` flag redirects to file.
6. **Completion**: Lint + test pass → commit & push.

## TDD Protocol (Rust)
- Write test first (RED: `cargo test` fails).
- Implement minimal code to pass (GREEN: `cargo test` passes).
- Clean up, extract, document (REFACTOR: no new tests, verify pass).
- No `.unwrap()` in production code. `.expect()` only in tests.

## Git Protocol
- **Message Format**: `feat(html2md): <desc>`, `fix(html2md): <desc>`, `chore(html2md): <desc>`
- **Command**: `git add . && git commit -m "<message>" && git push`

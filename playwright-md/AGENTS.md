# Pi playwright-md

This file defines coding standards, command protocols, and autonomous behavior for the playwright-md skill.

## Architecture
- Single-binary CLI (`playwright-md`) orchestrating Playwright + html2md via Rust crate imports.
- Linear pipeline: navigate → wait → extract → sanitize → convert → output.
- Zero subprocess forks — direct crate API calls.
- See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for stack, module layout, and design decisions.

## Plan
See [`PLAN.md`](./PLAN.md) for roadmap and milestones.
See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for architecture decisions.

## Project Scope
- **Focus**: URL → Markdown in single command. JS-rendered pages supported.
- **Goal**: Eliminate 2-step manual piping. One invocation, one output.
- **Dependencies**: `playwright` crate (browser), `comrak` crate (converter), `ammonia` crate (sanitizer).

## Core Commands
- **Build**: `cargo build --release`
- **Basic**: `./target/release/playwright-md --url <URL> --action page-to-md`
- **To file**: `./target/release/playwright-md --url <URL> --action page-to-md --output result.md`
- **With auth**: `./target/release/playwright-md --url <URL> --cookies '[{"name":"x","value":"y"}]'`
- **Core only**: `./target/release/playwright-md --url <URL> --core-only`
- **Core + selector**: `./target/release/playwright-md --url <URL> --core-selector '#main'`
- **Tests**: `cargo test`

## Behavior & Workflow
1. **URL Required**: `page-to-md` action requires `--url`. No URL → error, no guess.
2. **Wait Before Extract**: Always honor `--wait-for` / `--wait-for-url` before extracting HTML.
3. **Sanitize Pre-Convert**: Strip `<script>`, `<style>`, `<noscript>` tags before comrak pipeline. Default behavior.
4. **Error Handling**: `thiserror` + `?` operator. Log to stderr via `tracing`, exit code 1. Agent can retry with `--retries`.
5. **Cleanup**: `browser.close()` in `Drop` impl + explicit `await`. No orphan Chromium processes.
6. **Output**: Markdown to stdout by default. `--output` redirects to file.
7. **Completion**: `cargo clippy` clean + `cargo test` pass → commit & push.

## Git Protocol
- **Message Format**: `feat(playwright-md): <desc>`, `fix(playwright-md): <desc>`, `chore(playwright-md): <desc>`
- **Command**: `git add . && git commit -m "<message>" && git push`

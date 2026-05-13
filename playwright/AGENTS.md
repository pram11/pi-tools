# Pi Playwright

This file defines coding standards, command protocols, and autonomous behavior for the Playwright skill.

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for module layout, dispatch, session model.
See [`PLAN.md`](./PLAN.md) for roadmap and milestones.

## Project Scope
- **Focus**: Headless browser automation — navigation, interaction, extraction, screenshots.
- **Goal**: Agent-runnable UI automation with deterministic pass/fail signals.
- **Language**: Rust (migrated from Python).

## Core Commands
- **Build**: `cargo build --release`
- **Setup**: `cargo install playwright-bin || npx playwright install chromium`
- **Run action**: `cargo run -- --url <URL> <action> [--selector <CSS>] [--value <text>]`
- **Session start**: `cargo run -- session-start --url <URL>`
- **Session stop**: `cargo run -- session-stop`
- **Tests**: `cargo test`

## TDD Protocol: Red → Green → Refactor
- **RED**: Write a failing test first. `cargo test <name>` → must FAIL. Defines expected behavior.
- **GREEN**: Minimal implementation to pass. `cargo test <name>` → must PASS. No over-engineering.
- **REFACTOR**: Clean up code, extract helpers, improve types. `cargo test` → must still PASS. No behavior change.
- **Cycle**: Every new action/feature follows R→G→R. No commits with untested code.
- **Coverage**: Each action module has a companion `#[cfg(test)]` module.
- **CI Gate**: `cargo test` must pass before `git commit`. Exit code 1 on test failure.

## Behavior & Workflow
1. **URL First**: Always target a URL before interacting. No URL → error, no guess.
2. **Selectors Over Fragile Waits**: Use explicit CSS selectors. Prefer `wait_for_selector` or action auto-wait.
3. **Stateful When Needed**: Multi-step flows → use session mode (`session-start` / `session-stop`).
4. **Error Handling**: Wrap every action in Result. Log to stderr, exit code 1 on failure.
5. **Cleanup**: Browser close in every path. No orphan Chromium processes.
6. **Completion**: `cargo test` + `cargo clippy` pass → commit & push.

## Git Protocol
- **Message Format**: `feat(playwright): <desc>`, `fix(playwright): <desc>`, `chore(playwright): <desc>`
- **Command**: `git add . && git commit -m "<message>" && git push`

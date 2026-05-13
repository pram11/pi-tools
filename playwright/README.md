# Playwright Skill

Headless Chromium browser automation via Playwright Rust API. 46 actions for E2E testing, scraping, form automation, and UI verification.

## Quick Start

```bash
cargo build --release
cargo run -- --url https://example.com navigate
cargo run -- --action screenshot --output page.png
```

## Actions (46)

Full reference → [SKILL.md](./SKILL.md)

| Tier | Actions |
|---|---|
| **Core** (8) | navigate, click, type, extract, screenshot, wait, eval, scroll |
| **Form** (4) | form-detect, smart-fill, submit, wizard |
| **Extraction** (4) | scrape, extract-all, network, pdf |
| **Assertions** (5) | expect-text, expect-visible, expect-url, screenshot-diff, report |
| **Advanced** (21) | shadow-*, iframe-*, dialog-*, upload, auth-*, tabs-* |

## Session Mode

Persistent browser context with cookie/localStorage persistence:

```bash
cargo run -- session-start --url https://example.com
cargo run -- --action click --selector "#btn"
cargo run -- --action extract --selector "h1"
cargo run -- session-stop
```

## Architecture

- Async Rust CLI (`src/main.rs`) driving headless Chromium
- Session state in SQLite (`.sessions/state.db`) + Playwright storage_state JSON
- Auto-recovery on page crash / navigation timeout (`--retries N`)
- All actions return to stdout (JSON or plain text); errors to stderr with exit code 1

## Testing

```bash
cargo test
```

## TDD Protocol

See [AGENTS.md](./AGENTS.md) — Red → Green → Refactor cycle enforced for all new actions.

## Project Scope

Headless browser automation — navigation, interaction, extraction, screenshots, assertions, form flows, data scraping, shadow DOM, iframes, dialogs, file upload, auth, multi-tab orchestration.

## License

MIT (inherited from pi-tools)

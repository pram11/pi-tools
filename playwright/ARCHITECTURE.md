# Playwright Skill — Architecture

## Stack
- **Language**: Rust 2021 edition
- **Runtime**: Async CLI (`tokio`), headless Chromium via `playwright` crate
- **State**: SQLite (`rusqlite`) + JSON storage_state (`.sessions/storage.json`)
- **CLI**: `clap` derive macros
- **Serialization**: `serde` / `serde_json`
- **Image diff**: `image` crate

## Module Layout

```
playwright/
├── Cargo.toml
├── src/
│   ├── main.rs                  # CLI entry, clap args, browser lifecycle, session commands
│   ├── actions/
│   │   ├── mod.rs               # CliArgs struct + dispatch() → 46 action handlers
│   │   ├── navigate.rs          # navigate
│   │   ├── interaction.rs       # click, type, wait, eval, scroll
│   │   ├── extract.rs           # extract, scrape, extract-all
│   │   ├── screenshot.rs        # screenshot, screenshot-diff
│   │   ├── form.rs              # form-detect, smart-fill, submit, wizard
│   │   ├── assertions.rs        # expect-text, expect-visible, expect-url, report
│   │   ├── network.rs           # network, pdf
│   │   ├── shadow.rs            # shadow-detect/query/click/fill/extract/pierce
│   │   ├── iframe.rs            # iframe-list/query/click/fill/extract
│   │   ├── dialog.rs            # dialog-accept/dismiss/prompt
│   │   ├── upload.rs            # upload, upload-detect
│   │   ├── auth.rs              # auth-inject, auth-clear
│   │   └── tabs.rs              # tabs-open/list/switch/close/close-all/broadcast/gather
│   ├── session/
│   │   ├── mod.rs               # Session struct, init_db, load/save/clear, storage paths
│   │   └── db.rs                # Schema docs
│   └── utils/
│       └── mod.rs               # extract_origin(), retry() with backoff
├── tests/
│   └── cli_actions.rs           # Binary + action registry tests
├── .sessions/
│   ├── state.db                 # SQLite: sessions table (singleton row)
│   └── storage.json             # Playwright storage_state (cookies + localStorage)
├── AGENTS.md
├── ARCHITECTURE.md
├── PLAN.md
├── README.md
└── SKILL.md
```

## Action Dispatch

`actions::dispatch(action, args, browser)` — single async fn matches on 46 action strings, routes to module function. All handlers share `CliArgs` struct (clap derive). Signature:

```rust
pub async fn action_xyz(page: &Page, args: &CliArgs) -> Result<()>
```

Context-level actions (auth-inject, tabs-*) receive `&BrowserContext` instead of `&Page`.

## Session Model

```sql
-- .sessions/state.db
CREATE TABLE sessions (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    url TEXT,
    title TEXT,
    cookies TEXT,          -- JSON array
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

Single-row singleton. `ON CONFLICT(id) DO UPDATE` for upserts. `storage.json` holds Playwright's `storage_state()` JSON (cookies + localStorage) for cross-invocation persistence.

## Dependencies

| Crate | Purpose |
|---|---|
| `playwright` | Headless Chromium driver (async) |
| `tokio` | Async runtime |
| `clap` | CLI arg parsing (derive macros) |
| `serde` / `serde_json` | JSON serialization |
| `rusqlite` | SQLite session persistence (bundled) |
| `image` | Screenshot diff (pixel comparison) |
| `url` | URL parsing / origin extraction |
| `anyhow` / `thiserror` | Error handling |

## Design Principles
1. **URL First** — No action without URL. No guessing.
2. **Selectors Over Waits** — Explicit CSS selectors, never arbitrary timeouts.
3. **Stateful When Needed** — Session mode for multi-step flows.
4. **Error Boundaries** — Every action returns `Result`. Stderr log, exit 1.
5. **No Orphans** — `browser.close()` in every exit path.
6. **TDD** — Red → Green → Refactor for every new action.

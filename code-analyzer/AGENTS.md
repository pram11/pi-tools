# AGENTS.md — Rust Code-Analyzer Conventions

## Build & Run
```bash
cargo build --release          # → target/release/code-analyzer
cargo run -- --path . --condensed
cargo test
```

## Code Style
- `rustfmt` on every commit
- `clippy` warnings = errors (`#![deny(warnings)]`)
- Snake case for modules/files, PascalCase for types/traits
- `Result<T, Error>` return types — no panics in analyzer logic
- `Box<dyn Analyzer>` for trait objects; prefer generics where possible

## Analyzer Contract (`src/analyzer.rs`)
All analyzers implement:
```rust
pub trait Analyzer: Send + Sync {
    fn languages(&self) -> &[&str];       // e.g. &[".py"]
    fn analyze(&self, target: &Path) -> Result<Vec<Finding>, Error>;
}
```

## Schema Rules (`src/schema.rs`)
- `Finding` struct is the canonical output unit — all analyzers emit this
- `feature_type` is enum: `Route | Component | Logic`
- `complexity_score` is always `u32`
- Optional fields (`loc`, `nesting_depth`, `routes`, `edges`) use `Option<T>`
- All structs derive `Serialize + Deserialize + Debug + Clone`

## Plugin Registry (`src/analyzers/mod.rs`)
- `PluginVec` struct holds `Vec<Box<dyn Analyzer>>`
- `PluginVec::new()` instantiates all known analyzers at runtime
- `PluginVec::filter(langs)` → filtered subset
- No dynamic loading — all analyzers compiled in

## tree-sitter Usage
- Parse → `Parser::new()` → `Parser::set_language()` → `Parser::parse()`
- Always handle parse errors gracefully (skip file, don't panic)
- Node iteration: `node.child_count()` + `node.child(i)` loop
- Text extraction: `node.utf8_text(source_code)` → `&str`
- Reuse `Parser` instance per-analyzer (thread-safe with `RwLock` if shared)

## File Walking (`src/lib/filter.rs`)
- `walkdir::DirEntry` with depth-first traversal
- Exclude dirs: `.git`, `node_modules`, `target`, `__pycache__`, `.venv`, etc.
- Wildcard exclusion support (e.g., `*.egg-info`)
- Return `Vec<PathBuf>`, sorted for deterministic output

## Error Handling
- `anyhow::Result<T>` in main.rs / CLI layer
- Custom `enum Error` in library modules
- `thiserror` for error derives
- Analyzer failures → `warn!` + skip file (never abort run)

## Testing
- Integration tests in `tests/` mirror Python test structure 1:1
- Use `tempfile` crate for temp project dirs
- Use `assert_json_diff` or manual JSON comparison
- Test names match Python equivalents: `test_extract_functions`, `test_route_discovery`, etc.

## Deployment
- `install_skill.sh`: `cargo build --release` → copy binary to `~/.pi/skills/`
- No venv, no pip — single binary
- `SKILL.md` updated: invocation via `./code-analyzer --path <dir>`

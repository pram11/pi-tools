# Implementation Roadmap: Code Insight Phase

## Phase 1: Core Scaffolding ✅ Done
- [x] Establish `code-analyzer/` directory structure.
- [x] Implement `main.py` with dynamic plugin discovery and loading.
- [x] Define the `BaseAnalyzer` abstract class in `base.py`.

## Phase 2: Analyzer Development ✅ Done
- [x] Build the `RegexAnalyzer` for baseline multi-language support.
- [x] Develop the `PythonASTAnalyzer` for high-fidelity Python mapping.
- [x] Create a `ProjectDetector` utility to automate plugin selection.

## Phase 3: Refinement & Integration ✅ Done
- [x] Standardize the JSON output for downstream E2E scenario generators.
- [x] Implement token-optimization logic to condense analysis results for LLM context windows.
- [x] Integrate with the `pi-mono` local skill registry.

## Phase 4: Automation & CI ✅ Done
- [x] Setup automated "Commit and Push" triggers for the agent upon task completion.
- [x] Add unit tests for each analyzer plugin.

## Phase 5: JS/TSX Deep Analysis ✅ Done
- [x] **JSXASTAnalyzer** — tree-sitter-based TSX/JSX parsing
- [x] **Identifier Extraction** — components, hooks, imports, exports
- [x] **Complexity Metrics** — cyclomatic complexity, LOC, nesting depth
- [x] **Route Discovery** — Next.js `app/` router patterns
- [x] **Cross-File Edges** — import/export relationships
- [x] **Output Schema Extension** — `identifiers`, `complexity`, `edges` for JS/TSX

## Phase 6: Rust Rewrite (Current)

### Context
Python codebase complete & functional. Rewrite to Rust for:
- **Performance**: tree-sitter parsing is already native-C; Rust eliminates Python overhead
- **Single Binary**: no venv, no pip deps → deploy via binary
- **Type Safety**: compile-time guarantees on analyzer contracts
- **Unified Backend**: `tree-sitter-python` replaces Python's `ast` module → one parser lib for all languages

### Rust Crate Structure
```
code-analyzer/
├── Cargo.toml
├── src/
│   ├── main.rs                  # CLI entry, plugin registry, orchestration
│   ├── analyzer.rs              # Analyzer trait + Finding/Edge schemas
│   ├── analyzers/
│   │   ├── mod.rs               # PluginVec registry, discover()
│   │   ├── regex.rs             # RegexAnalyzer (file discovery, baseline)
│   │   ├── python.rs            # PythonASTAnalyzer (tree-sitter-python)
│   │   └── jsx.rs               # JSXASTAnalyzer (tree-sitter-typescript)
│   ├── lib/
│   │   ├── mod.rs
│   │   ├── filter.rs            # File walker, exclusion logic
│   │   ├── report.rs            # E2E report builder
│   │   ├── condense.rs          # Token optimizer (condensed output)
│   │   └── detector.rs          # ProjectDetector (language detection)
│   └── schema.rs                # serde JSON schemas (Finding, Report, CondensedReport)
├── tests/
│   ├── plugin_discovery.rs
│   ├── python_ast.rs
│   ├── jsx_ast.rs
│   ├── output_schema.rs
│   ├── e2e_report.rs
│   ├── token_optimizer.rs
│   └── project_detector.rs
├── .gitignore
├── SKILL.md                     # Updated for binary invocation
├── install_skill.sh             # Updated: cargo build → cp binary
├── AGENTS.md                    # New: Rust dev conventions
├── ARCHITECTURE.md              # Updated: Rust architecture
└── PLAN.md                      # This file
```

### Key Dependencies
| Crate | Purpose |
|---|---|
| `clap` | CLI argument parsing (replaces argparse) |
| `serde` + `serde_json` | JSON serialization (replaces json module) |
| `tree-sitter` | Core AST parsing (replaces py-tree-sitter) |
| `tree-sitter-python` | Python grammar (replaces Python `ast`) |
| `tree-sitter-typescript` | TSX/JSX grammar (same as current) |
| `walkdir` | Directory traversal (replaces pathlib.rglob) |
| `chrono` | Timestamps (replaces datetime) |
| `regex` | Pattern matching (shared with RegexAnalyzer) |

### Migration Checklist
- [x] 6.1 Initialize Cargo project (`cargo init --name code-analyzer`)
- [x] 6.2 Define `schema.rs` — `Finding`, `Edge`, `Report`, `CondensedReport` structs
- [x] 6.3 Define `analyzer.rs` — `Analyzer` trait (replaces `BaseAnalyzer`)
- [x] 6.4 Implement `lib/filter.rs` — `iter_sources()`, exclusion logic
- [x] 6.5 Implement `lib/detector.rs` — `ProjectDetector::detect()`
- [x] 6.6 Implement `lib/report.rs` — `build_report()`
- [x] 6.7 Implement `lib/condense.rs` — `condense_report()`
- [x] 6.8 Implement `analyzers/regex.rs` — `RegexAnalyzer`
- [x] 6.9 Implement `analyzers/python.rs` — `PythonAnalyzer` (tree-sitter-python)
- [x] 6.10 Implement `analyzers/jsx.rs` — `JSXAnalyzer` (tree-sitter-typescript)
- [x] 6.11 Implement `analyzers/mod.rs` — plugin registry + `discover()`
- [x] 6.12 Implement `main.rs` — CLI (clap), orchestration, JSON output
- [x] 6.13 Port tests (7 test modules → 7 integration tests) — **43 tests, all passing**
- [x] 6.14 Update `SKILL.md` — binary invocation, remove venv refs
- [x] 6.15 Update `install_skill.sh` — `cargo build --release` → binary deploy
- [x] 6.16 Update `ARCHITECTURE.md` — Rust architecture docs
- [x] 6.17 Update `AGENTS.md` — Rust development conventions
- [x] 6.18 Benchmark: verify parity with Python version
- [x] 6.19 Cleanup: remove `.py` files, `.venv/`, `requirements.txt`

### Parity Checklist (Python → Rust)
| Feature | Python | Rust Target |
|---|---|---|
| Plugin discovery | `importlib` dynamic | `Vec<Box<dyn Analyzer>>` registry |
| Python AST | `ast.parse()` | `tree-sitter-python` |
| TSX/JSX AST | `tree-sitter` (py) | `tree-sitter` (native) |
| File walking | `pathlib.rglob` | `walkdir` |
| JSON output | `json.dumps` | `serde_json` |
| CLI | `argparse` | `clap` |
| Lang detection | marker files + exts | same logic, Rust impl |
| Report builder | dict assembly | struct + `serde` |
| Token condense | dict group/merge | HashMap group/merge |

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

## Phase 7: Rust Analyzer

### Goal
Add `RustAnalyzer` — tree-sitter-rust based source mapping for `.rs` files.

### Dependency
| Crate | Purpose |
|---|---|
| `tree-sitter-rust` | Rust grammar (v0.21+ to match existing `tree-sitter` 0.22) |

### Implementation Checklist
- [x] 7.1 Add `tree-sitter-rust` to `Cargo.toml` dependencies
- [x] 7.2 Create `src/analyzers/rust.rs` — `RustAnalyzer` struct + `Analyzer` impl
- [x] 7.2.1 `fn rust_language()` → `tree_sitter_rust::language()`
- [x] 7.2.2 `new()` → `Mutex<Parser>` with rust language set
- [x] 7.2.3 `walk_ast()` → traverse AST, extract:
  - `function_item` → `FeatureType::Logic` (identifiers)
  - `struct_item` → `FeatureType::Component` (identifiers)
  - `enum_item` → `FeatureType::Component` (identifiers + variant names)
  - `impl_item` → nest methods under struct/enum name (e.g. `MyStruct.method`)
  - `trait_item` → `FeatureType::Component` (identifiers)
  - `use_declaration` → import edges
- [x] 7.2.4 `count_complexity()` → branch nodes: `if_expression`, `loop_expression`, `for_expression`, `while_expression`, `match_expression`, `binary_expression` (&&/||)
- [x] 7.2.5 `extract_edges()` → `use_declaration` / `scoped_identifier` / `scoped_use_list` → `Edge { edge_type: "import", name, source }`
- [x] 7.2.6 `languages()` → `&[".rs"]`
- [x] 7.3 Update `src/analyzers/mod.rs` — add `mod rust;`, `pub use rust::RustAnalyzer;`, register in `discover()`
- [x] 7.4 Create `tests/rust_ast.rs` — integration tests (9 tests, all passing):
  - `test_extract_functions` — `fn hello() {}`
  - `test_extract_structs` — `struct Foo { ... }`
  - `test_extract_enums` — `enum Bar { A, B }` → `Bar.A`, `Bar.B`
  - `test_extract_impl_methods` — `impl Foo { fn bar() {} }` → `Foo.bar`
  - `test_extract_traits` — `trait TraitName { fn draw(); }` → `TraitName.draw`
  - `test_extract_imports` — `use std::collections::HashMap;`
  - `test_complexity_score_set` — assert `complexity_score > 1`
  - `test_ignores_non_rust_files` — `.md` files → empty findings
  - `test_languages_includes_rs` — `.rs` in languages list
- [x] 7.5 Update `src/util/filter.rs` — add `.cargo` to `DEFAULT_EXCLUDE_DIRS`
- [x] 7.6 Run `cargo build --release` — verify clean build
- [x] 7.7 Run `cargo test` — all 52 tests pass (43 existing + 9 new)
- [x] 7.8 Benchmark: self-analysis → 54 files, 136 identifiers, languages: [python, rust] ✅

### tree-sitter-rust Node Types (Key AST Nodes)
| Node Kind | Meaning | Mapping |
|---|---|---|
| `function_item` | `fn name(...) { ... }` | `Logic` identifier |
| `struct_item` | `struct Name { ... }` | `Component` identifier |
| `enum_item` | `enum Name { ... }` | `Component` identifier + variants |
| `impl_item` | `impl Name { ... }` | Nest child functions as `Name.fn` |
| `trait_item` | `trait Name { ... }` | `Component` identifier |
| `use_item` | `use path::...` | `Edge` (import) |
| `if_expression` | `if ...` | complexity +1 |
| `match_expression` | `match ...` | complexity +1 per arm |
| `for_expression` | `for x in ...` | complexity +1 |
| `while_expression` | `while ...` | complexity +1 |
| `loop_expression` | `loop { ... }` | complexity +1 |
| `binary_expression` | `&&` / `\|\|` | complexity +1 |
| `macro_invocation` | `macro!()` | skip (not a function) |
| `mod_item` | `mod name;` | skip (module decl) |
| `type_item` | `type Alias = ...` | `Component` (optional) |

### Complexity Scoring (Rust-specific)
```
base score: 1
+1 per: if, match, for, while, loop, &&, ||
+1 per: match arm
```

### Edge Extraction (Rust-specific)
```
use std::collections::HashMap;
  → Edge { type: "import", name: "HashMap", source: "std::collections" }

use serde::{Serialize, Deserialize};
  → Edge { type: "import", name: "Serialize", source: "serde" }
  → Edge { type: "import", name: "Deserialize", source: "serde" }

use crate::module::MyType;
  → Edge { type: "import", name: "MyType", source: "crate::module" }
```

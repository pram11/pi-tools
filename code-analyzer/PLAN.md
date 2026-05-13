# Implementation Roadmap: Code Analyzer (Rust)

## Phase 1: Core Scaffolding ✅ Done
- [x] Initialize Cargo project (`cargo init --name code-analyzer`)
- [x] Define `schema.rs` — `Finding`, `Edge`, `Report`, `CondensedReport` structs
- [x] Define `analyzer.rs` — `Analyzer` trait (`Send + Sync`)

## Phase 2: Analyzer Development ✅ Done
- [x] Implement `lib/filter.rs` — `iter_sources()`, exclusion logic (walkdir)
- [x] Implement `lib/detector.rs` — `ProjectDetector::detect()`
- [x] Implement `lib/report.rs` — `build_report()`
- [x] Implement `lib/condense.rs` — `condense_report()` (token optimizer)
- [x] Implement `analyzers/regex.rs` — `RegexAnalyzer` (multi-language baseline)
- [x] Implement `analyzers/python.rs` — `PythonAnalyzer` (tree-sitter-python)
- [x] Implement `analyzers/jsx.rs` — `JSXAnalyzer` (tree-sitter-typescript)
- [x] Implement `analyzers/mod.rs` — `PluginVec` registry + `discover()`

## Phase 3: CLI & Integration ✅ Done
- [x] Implement `main.rs` — CLI (clap), orchestration, JSON output
- [x] Standardize JSON output (serde-serialized) for downstream E2E scenario generators
- [x] Integrate with `pi-mono` local skill registry

## Phase 4: Testing & CI ✅ Done
- [x] Port 7 integration test modules (43 tests, all passing)
- [x] Update `install_skill.sh` — `cargo build --release` → binary deploy
- [x] Update `SKILL.md` — binary invocation

## Phase 5: JS/TSX Deep Analysis ✅ Done
- [x] **JSXAnalyzer** — tree-sitter-typescript TSX/JSX parsing
- [x] **Identifier Extraction** — components, hooks, imports, exports
- [x] **Complexity Metrics** — cyclomatic complexity, LOC, nesting depth
- [x] **Route Discovery** — Next.js `app/` router patterns
- [x] **Cross-File Edges** — import/export relationships
- [x] **Output Schema Extension** — `identifiers`, `complexity`, `edges` for JS/TSX

## Phase 6: Rust Analyzer ✅ Done

### Goal
Add `RustAnalyzer` — tree-sitter-rust based source mapping for `.rs` files.

### Dependency
| Crate | Purpose |
|---|---|
| `tree-sitter-rust` | Rust grammar (v0.21+ to match existing `tree-sitter` 0.22) |

### Implementation Checklist
- [x] 6.1 Add `tree-sitter-rust` to `Cargo.toml` dependencies
- [x] 6.2 Create `src/analyzers/rust.rs` — `RustAnalyzer` struct + `Analyzer` impl
- [x] 6.2.1 `fn rust_language()` → `tree_sitter_rust::language()`
- [x] 6.2.2 `new()` → `Mutex<Parser>` with rust language set
- [x] 6.2.3 `walk_ast()` → traverse AST, extract:
  - `function_item` → `FeatureType::Logic` (identifiers)
  - `struct_item` → `FeatureType::Component` (identifiers)
  - `enum_item` → `FeatureType::Component` (identifiers + variant names)
  - `impl_item` → nest methods under struct/enum name (e.g. `MyStruct.method`)
  - `trait_item` → `FeatureType::Component` (identifiers)
  - `use_declaration` → import edges
- [x] 6.2.4 `count_complexity()` → branch nodes: `if_expression`, `loop_expression`, `for_expression`, `while_expression`, `match_expression`, `binary_expression` (&&/||)
- [x] 6.2.5 `extract_edges()` → `use_declaration` / `scoped_identifier` / `scoped_use_list` → `Edge { edge_type: "import", name, source }`
- [x] 6.2.6 `languages()` → `&[".rs"]`
- [x] 6.3 Update `src/analyzers/mod.rs` — add `mod rust;`, `pub use rust::RustAnalyzer;`, register in `discover()`
- [x] 6.4 Create `tests/rust_ast.rs` — integration tests (9 tests, all passing):
  - `test_extract_functions` — `fn hello() {}`
  - `test_extract_structs` — `struct Foo { ... }`
  - `test_extract_enums` — `enum Bar { A, B }` → `Bar.A`, `Bar.B`
  - `test_extract_impl_methods` — `impl Foo { fn bar() {} }` → `Foo.bar`
  - `test_extract_traits` — `trait TraitName { fn draw(); }` → `TraitName.draw`
  - `test_extract_imports` — `use std::collections::HashMap;`
  - `test_complexity_score_set` — assert `complexity_score > 1`
  - `test_ignores_non_rust_files` — `.md` files → empty findings
  - `test_languages_includes_rs` — `.rs` in languages list
- [x] 6.5 Update `src/util/filter.rs` — add `.cargo` to `DEFAULT_EXCLUDE_DIRS`
- [x] 6.6 Run `cargo build --release` — verify clean build
- [x] 6.7 Run `cargo test` — all 52 tests pass (43 existing + 9 new)
- [x] 6.8 Benchmark: self-analysis → 54 files, 136 identifiers, languages: [python, rust] ✅

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

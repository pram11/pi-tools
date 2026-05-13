# Architecture: Plug-and-Play Code Analysis (Rust)

## Design Philosophy
**Trait-based Strategy Pattern**. The `Analyzer` trait decouples orchestration from language-specific parsing. Plugins registered at compile-time via `PluginVec`. Single static binary — zero runtime dependencies.

## Structural Components

### 1. CLI Entry (`src/main.rs`)
- `clap`-based argument parsing (`--path`, `--lang`, `--condensed`)
- Orchestrates: plugin discovery → analysis → report → output
- Single `cargo build --release` binary

### 2. Analyzer Trait (`src/analyzer.rs`)
```rust
pub trait Analyzer {
    fn languages(&self) -> &[&str];
    fn analyze(&self, target: &Path) -> Result<Vec<Finding>, Error>;
}
```
Replaces Python `BaseAnalyzer` ABC. Compile-time contract enforcement.

### 3. Data Schema (`src/schema.rs`)
- `Finding` — per-file analysis result (serde-serialized)
- `Edge` — import/export relationships
- `Report` — full output with metadata + findings + summary
- `CondensedReport` — token-optimized grouped output

### 4. Plugin Layer (`src/analyzers/`)
| Module | Language(s) | Backend |
|---|---|---|
| `regex.rs` | `.py`, `.java`, `.go`, `.rs`, `.rb`, `.c`, `.cpp`, `.h` | File discovery + baseline entries |
| `python.rs` | `.py` | `tree-sitter-python` — functions, classes, complexity |
| `jsx.rs` | `.tsx`, `.jsx` | `tree-sitter-typescript` — routes, components, hooks, imports, nesting |

### 5. Library (`src/lib/`)
| Module | Purpose |
|---|---|
| `filter.rs` | `iter_sources()` — walkdir + exclusion logic |
| `report.rs` | `build_report()` — wrap findings in structured report |
| `condense.rs` | `condense_report()` — group by feature_type, relative paths |
| `detector.rs` | `ProjectDetector::detect()` — marker files + extension fallback |

## Directory Structure
```
code-analyzer/
├── Cargo.toml
├── src/
│   ├── main.rs                  # CLI + orchestration
│   ├── analyzer.rs              # Analyzer trait
│   ├── schema.rs                # serde data models
│   ├── analyzers/
│   │   ├── mod.rs               # PluginVec registry
│   │   ├── regex.rs
│   │   ├── python.rs
│   │   └── jsx.rs
│   └── lib/
│       ├── mod.rs
│       ├── filter.rs
│       ├── report.rs
│       ├── condense.rs
│       └── detector.rs
├── tests/                       # Integration tests (1:1 with Python)
├── SKILL.md
├── install_skill.sh
└── .gitignore
```

## Data Flow
```
CLI args → PluginVec::discover() → [Analyzer]
                              ↓
                for each plugin: analyze(target)
                              ↓
                findings: Vec<Finding>
                              ↓
                build_report(target, findings) → Report
                              ↓ (if --condensed)
                condense_report(report) → CondensedReport
                              ↓
                serde_json::to_string_pretty() → stdout
```

## Dependencies
```toml
clap = { version = "4", features = ["derive"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
tree-sitter = "0.22"
tree-sitter-python = "0.21"
tree-sitter-typescript = "0.21"
walkdir = "2"
chrono = { version = "0.4", features = ["serde"] }
regex = "1"
```

## JSON Output Schema (unchanged from Python)

### Standard
```json
{
  "metadata": { "target": "...", "languages": [...], "total_files": N, "total_findings": N, "generated_at": "..." },
  "findings": [
    {
      "file_path": "...",
      "feature_type": "Route | Component | Logic",
      "identifiers": ["..."],
      "complexity_score": N
    }
  ],
  "summary": { "avg_complexity": N, "max_complexity": N, "min_complexity": N }
}
```

### Condensed
```json
{
  "metadata": { "target": "...", "languages": [...] },
  "grouped": { "Route": { "identifiers": [...], "files": [...] }, ... },
  "summary": { "avg": N, "max": N, "min": N },
  "total_files": N
}
```

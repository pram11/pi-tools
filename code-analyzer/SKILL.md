---
name: code-analyzer
description: Performs deep static analysis of a codebase to generate a feature chart containing routes, UI selectors, and structural metadata.
version: 0.3.0
---

# Code Analyzer Skill

Rust static binary — zero runtime deps. Single binary deploy.

## Usage

```bash
code-analyzer --path <directory_path> [--lang <.py,.tsx>] [--condensed]
```

### Arguments
- `--path` — Target directory or file to analyze (default: `.`)
- `--lang` — Comma-separated language filter (e.g. `.py,.tsx`). If omitted, all matching analyzers run.
- `--condensed` — Output compact report grouped by feature type (optimized for LLM context windows).

## Analyzer Plugins
| Plugin | Language(s) | Method |
|---|---|---|
| `PythonAnalyzer` | `.py` | tree-sitter-python — functions, classes, complexity |
| `JsxAnalyzer` | `.tsx`, `.jsx` | tree-sitter-typescript — routes (Next.js `app/`), components, hooks, imports, nesting depth |
| `RegexAnalyzer` | `.py`, `.java`, `.go`, `.rs`, `.rb`, `.c`, `.cpp`, `.h` | Fallback — file discovery, baseline entries |

## Output Schema (JSON)

### Standard
```json
{
  "metadata": { "target": "...", "languages": [...], "total_files": N, "total_findings": N, "generated_at": "..." },
  "findings": [
    {
      "file_path": "...",
      "feature_type": "Route" | "Component" | "Logic",
      "identifiers": ["..."],
      "complexity_score": N
    }
  ],
  "summary": { "avg_complexity": N, "max_complexity": N, "min_complexity": N }
}
```

### Condensed (`--condensed`)
```json
{
  "metadata": { "target": "...", "languages": [...] },
  "grouped": {
    "Route": { "identifiers": [...], "files": [...] },
    "Component": { ... },
    "Logic": { ... }
  },
  "summary": { "avg": N, "max": N, "min": N },
  "total_files": N
}
```

## Build
```bash
cargo build --release
# Binary: target/release/code-analyzer
```

## Test
```bash
cargo test
```

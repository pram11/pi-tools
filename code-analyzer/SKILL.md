---
name: code-analyst
description: Performs deep static analysis of a codebase to generate a feature chart containing routes, UI selectors, and structural metadata.
version: 0.2.0
---

# Code Analyst Skill

This skill allows the agent to autonomously map the functional surface area of any source code directory.

## Usage
The agent invokes the skill via the CLI:

```bash
python main.py --path <directory_path> [--lang <py,tsx>] [--condensed]
```

### Arguments
- `--path` — Target directory or file to analyze (default: `.`)
- `--lang` — Comma-separated language filter (e.g. `py,tsx`). If omitted, all matching plugins run.
- `--condensed` — Output compact report grouped by feature type (optimized for LLM context windows).

## Analyzer Plugins
| Plugin | Language(s) | Method |
|---|---|---|
| `PythonASTAnalyzer` | `.py` | Python `ast` module — functions, classes, complexity |
| `JSXASTAnalyzer` | `.tsx`, `.jsx` | tree-sitter — routes (Next.js `app/`), components, hooks, imports, nesting depth |
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
      // optional (JSXASTAnalyzer):
      // "loc": N, "nesting_depth": N, "routes": ["..."], "edges": [{"type","name","source"}]
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

## Setup
```bash
pip install -r requirements.txt
```
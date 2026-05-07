---
name: code-analyzer
description: "Static code analysis skill. Use to detect code smells, estimate complexity, check dependencies, and enforce best practices in a codebase."
---

# Code Analyzer

Performs static analysis on target codebases. Detects cyclomatic complexity, unused imports, deep nesting, and potential bottlenecks.

## Setup
```bash
cd ~/.pi/skills/code-analyzer
python -m venv .venv
.venv/bin/pip install -r requirements.txt
```

## Usage
Run via isolated venv:
```bash
~/.pi/skills/code-analyzer/.venv/bin/python ~/.pi/skills/code-analyzer/scripts/analyze.py <TARGET_PATH> [--lang python,javascript] [--depth 3]
```

### Options
| Flag | Description |
|------|-------------|
| `<TARGET_PATH>` | Directory or file to analyze (required) |
| `--lang` | Comma-separated languages (default: all detected) |
| `--depth` | Max nesting depth warning threshold (default: 4) |
| `--format` | Output format: `json` or `markdown` (default: markdown) |

## Output
Generates analysis report including:
- File count / LOC summary
- Cyclomatic complexity hotspots
- Unused imports / dead code
- Dependency graph (if available)
- Actionable recommendations

---
name: code-analyzer
description: Performs deep static analysis of a codebase to generate a feature chart containing routes, UI selectors, and structural metadata.
version: 0.1.0
---

# Code Analyzer Skill

Autonomously maps the functional surface area of any source code directory. Single binary, no venv, no pip.

## Installation

```bash
# Build release binary
cargo build --release

# Move built binary to skill root
cp target/release/code-analyzer .pi/skills/code-analyzer/code-analyzer
chmod +x .pi/skills/code-analyzer/code-analyzer
```

## Usage

```bash
./code-analyzer --path <directory_path>
./code-analyzer --path <directory_path> --condensed
./code-analyzer --path <directory_path> --lang ".py,.tsx"
```

## Options

| Flag | Description |
|---|---|
| `--path` | Target directory or file (default: `.`) |
| `--lang` | Comma-separated language filter (e.g. `.py,.tsx`) |
| `--condensed` | Condense output for LLM context windows |
| `--help` | Print help |

## Binary

Self-contained Rust binary located at skill root (`code-analyzer`). No runtime dependencies.

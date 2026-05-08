# Pi Agent Knowledge Base

Local SQLite vector DB skill for Pi Agent. Index code/documents with embeddings, search semantically via hybrid vector + FTS5.

## Overview

| Aspect | Detail |
|--------|--------|
| **Purpose** | Pi Agent self-manages knowledge via CRUD on local vector DB |
| **Storage** | Global scope: `~/.pi/agent-memory/knowledge.db` |
| **Embedding** | `nomic-embed-text-v1.5` (Q4_K_M GGUF, ~80MB) via `llama-cpp-python` |
| **Chunking** | `tree-sitter` AST-based (Python, JS/TS, Rust, Go) |
| **Search** | Hybrid cosine similarity + FTS5 keyword match |
| **Isolation** | Dedicated `.venv` at `~/.pi/skills/knowledge-base/.venv/` |

## Architecture

```
knowledge-base/
├── SKILL.md                 # Agent-facing control spec
├── ARCHITECTURE.md          # Design decisions & folder structure
├── AGENTS.md                # Project overview, workflow rules (Korean)
├── PLAN.md                  # Implementation plan (all phases ✅)
├── requirements.txt         # Python dependencies
├── install_skill.sh         # Global deployment script
├── models/
│   └── nomic-embed-text-v1.5.Q4_K_M.gguf   # Pre-downloaded embedding model
├── scripts/
│   ├── init_db.py           # DB init: sqlite-vec + FTS5 schema
│   ├── create.py            # [C] Chunk → embed → INSERT
│   ├── search.py            # [R] Hybrid vector + FTS5 search
│   ├── update.py            # [U] Delete old chunks → re-create
│   ├── delete.py            # [D] Remove by file/dir/pattern
│   └── core/
│       ├── db_client.py     # SQLite connection + sqlite-vec extension
│       ├── chunker.py       # tree-sitter AST parsing & chunking
│       └── embedder.py      # llama-cpp-python embedding extraction
└── .pi/skills/knowledge-base/   # Local skill registration (symlink/copy)
```

## Quick Start

### 1. Install Skill

```bash
./install_skill.sh
```

Copies skill to `~/.pi/skills/knowledge-base/`, installs deps into isolated `.venv`.

### 2. Initialize Database

```bash
~/.pi/skills/knowledge-base/.venv/bin/python \
  ~/.pi/skills/knowledge-base/scripts/init_db.py
```

Creates `~/.pi/agent-memory/knowledge.db` with `sqlite-vec` + FTS5 tables.

### 3. CRUD Operations

```bash
# Alias for brevity
PY=~/.pi/skills/knowledge-base/.venv/bin/python
SKILL=~/.pi/skills/knowledge-base/scripts

# CREATE — Index a file
$PY $SKILL/create.py /path/to/your/file.py

# SEARCH — Semantic + keyword hybrid search
$PY $SKILL/search.py "authentication logic" --top-k 5
$PY $SKILL/search.py "authentication logic" --fuzzy          # FTS5 fuzzy match

# UPDATE — Refresh file in DB
$PY $SKILL/update.py /path/to/your/file.py

# DELETE — Remove by file, directory, or glob pattern
$PY $SKILL/delete.py /path/to/your/file.py
$PY $SKILL/delete.py /path/to/your/dir/
$PY $SKILL/delete.py . --pattern "*.test.js"
```

## Dependencies

| Package | Purpose |
|---------|---------|
| `sqlite-vec` | In-process vector storage + cosine similarity |
| `tree-sitter` + language parsers | AST-based code chunking (PY/JS/TS/Rust/Go) |
| `llama-cpp-python` | Local GGUF embedding inference |
| `huggingface_hub` | Auto-download model if missing |
| `numpy` | Vector math utilities |

Install: `~/.pi/skills/knowledge-base/.venv/bin/pip install -r requirements.txt`

## Supported Languages

| Language | Parser |
|----------|--------|
| Python | `tree-sitter-python` |
| JavaScript / JSX | `tree-sitter-javascript` |
| TypeScript / TSX | `tree-sitter-typescript` |
| Rust | `tree-sitter-rust` |
| Go | `tree-sitter-go` |

## Key Design Decisions

1. **Global scope storage** — Single `knowledge.db` shared across all projects (`~/.pi/agent-memory/`)
2. **Script-based execution** — Agent calls pre-built scripts via CLI, never generates ad-hoc Python
3. **Auto-download models** — GGUF model downloaded via `huggingface_hub` if not present in `models/`
4. **Isolated venv** — All deps in skill's own `.venv`, no pollution of project environments

## Docs

- **SKILL.md** — Agent-facing CRUD spec & usage examples
- **ARCHITECTURE.md** — Folder structure, design rationale, ADRs
- **PLAN.md** — Implementation roadmap (all phases complete ✅)
- **AGENTS.md** — Project context, workflow rules, Git conventions

## License

Private / Internal

---
name: knowledge-base
description: "Manages a local SQLite vector database (Knowledge Base). Use this skill to index code, search for knowledge, update, or delete existing entries."
---

# Knowledge Base CRUD Operations Guide

When a user instructs you to register, update, delete, or query knowledge in the database, follow these procedures. All operations are performed by executing internal Python scripts that manipulate the SQLite database files.

## 1. Create (Index)
- Read the specified code files or documents and parse them into function/class units using `tree-sitter`.
- Execute the embedding script (based on `llama-cpp-python`) to extract vector representations for each unit.
- Perform a secure SQLite transaction to `INSERT` the extracted vectors along with metadata (e.g., file path, type).

## 2. Search (Retrieve)
- Convert the user's question or search query into an embedding using the embedding script.
- `SELECT` the top 5 documents from the database with the highest cosine similarity to use as context for the model.

## 3. Update (Refresh)
- Based on the file path where the knowledge has been updated, first perform the **Delete** operation to remove all previous vector data.
- Subsequently, re-run the **Create** operation with the new content to ensure the database is up to date.

## 4. Delete (Remove)
- Based on the file or directory path specified by the user for removal, execute a `DELETE` query against the corresponding records in the database.

## Usage Examples

Always use the isolated venv Python interpreter. Base path: `~/.pi/agent/skills/knowledge-base/`

### Init Database (One-time setup)
```bash
~/.pi/agent/skills/knowledge-base/.venv/bin/python ~/.pi/agent/skills/knowledge-base/scripts/init_db.py
```

### Create (Index a file)
```bash
~/.pi/agent/skills/knowledge-base/.venv/bin/python ~/.pi/agent/skills/knowledge-base/scripts/create.py <FILE_PATH>
# Example:
~/.pi/agent/skills/knowledge-base/.venv/bin/python ~/.pi/agent/skills/knowledge-base/scripts/create.py /home/ash/Documents/dev/test_web/src/main.ts
```

### Search (Retrieve)
```bash
~/.pi/agent/skills/knowledge-base/.venv/bin/python ~/.pi/agent/skills/knowledge-base/scripts/search.py <QUERY> [--top-k N]
# Example:
~/.pi/agent/skills/knowledge-base/.venv/bin/python ~/.pi/agent/skills/knowledge-base/scripts/search.py "authentication logic" --top-k 5
```

### Update (Refresh a file)
```bash
~/.pi/agent/skills/knowledge-base/.venv/bin/python ~/.pi/agent/skills/knowledge-base/scripts/update.py <FILE_PATH>
# Example:
~/.pi/agent/skills/knowledge-base/.venv/bin/python ~/.pi/agent/skills/knowledge-base/scripts/update.py /home/ash/Documents/dev/test_web/src/main.ts
```

### Delete (Remove by file or directory)
```bash
# Single file:
~/.pi/agent/skills/knowledge-base/.venv/bin/python ~/.pi/agent/skills/knowledge-base/scripts/delete.py /home/ash/Documents/dev/test_web/src/main.ts

# Whole directory:
~/.pi/agent/skills/knowledge-base/.venv/bin/python ~/.pi/agent/skills/knowledge-base/scripts/delete.py /home/ash/Documents/dev/test_web/src/

# Glob pattern:
~/.pi/agent/skills/knowledge-base/.venv/bin/python ~/.pi/agent/skills/knowledge-base/scripts/delete.py . --pattern "*.test.js"
```

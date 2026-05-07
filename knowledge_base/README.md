# Knowledge Base Skill

Local SQLite vector DB skill for Pi Agent.

## Usage

```bash
# Initialize DB
python scripts/init_db.py

# CRUD
python scripts/create.py <file_path>
python scripts/search.py "<query>"
python scripts/update.py <file_path>
python scripts/delete.py <file_path>
```

## ADR

- **Storage scope**: B — project-local (`./.pi/knowledge.db`)
- **Embedding model**: A — pre-download GGUF to `models/`

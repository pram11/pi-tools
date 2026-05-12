import sqlite3
from pathlib import Path
from typing import Optional

import sqlite_vec

DB_DIR = Path.home() / ".pi" / "agent-memory"
DB_PATH = DB_DIR / "knowledge.db"

def get_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    target = db_path or DB_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(target))
    sqlite_vec.load(conn)
    conn.row_factory = sqlite3.Row
    return conn

def init_schema(conn: sqlite3.Connection) -> None:
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding FLOAT[768],
            metadata TEXT,
            UNIQUE(file_path, chunk_index)
        );
        CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(content, content=knowledge_base, content_rowid=id);
        CREATE TRIGGER IF NOT EXISTS kb_ai AFTER INSERT ON knowledge_base BEGIN
            INSERT INTO knowledge_fts(rowid, content) VALUES (new.id, new.content);
        END;
        CREATE TRIGGER IF NOT EXISTS kb_ad AFTER DELETE ON knowledge_base BEGIN
            INSERT INTO knowledge_fts(knowledge_fts, rowid, content) VALUES ('delete', old.id, old.content);
        END;
        CREATE TRIGGER IF NOT EXISTS kb_au AFTER UPDATE ON knowledge_base BEGIN
            INSERT INTO knowledge_fts(knowledge_fts, rowid, content) VALUES ('delete', old.id, old.content);
            INSERT INTO knowledge_fts(rowid, content) VALUES (new.id, new.content);
        END;
    """)
    conn.commit()

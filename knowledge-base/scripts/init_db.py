#!/usr/bin/env python3
"""Initialize knowledge base SQLite DB with sqlite-vec and FTS5 schema."""
import sys
from pathlib import Path

# Allow importing from parent
sys.path.insert(0, str(Path(__file__).parent))

from core.db_client import get_connection, init_schema

def main():
    conn = get_connection()
    init_schema(conn)
    print(f"[init_db] DB initialized at {conn.execute('PRAGMA database_list').fetchone()[2]}")
    conn.close()

if __name__ == "__main__":
    main()

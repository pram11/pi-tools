#!/usr/bin/env python3
"""Delete: Remove all chunks matching file_path or directory pattern."""
import sys
import fnmatch
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.db_client import get_connection


def main():
    if len(sys.argv) < 2:
        print("[delete] Usage: delete.py <file_or_dir_path> [--pattern GLOB]")
        sys.exit(1)

    target = Path(sys.argv[1]).resolve()
    pattern = None

    for i, arg in enumerate(sys.argv[2:], 2):
        if arg == "--pattern" and i < len(sys.argv) - 1:
            pattern = sys.argv[i + 1]

    conn = get_connection()
    deleted = 0

    if pattern:
        # Glob-based deletion
        all_paths = [row["file_path"] for row in conn.execute("SELECT DISTINCT file_path FROM knowledge_base").fetchall()]
        matches = [p for p in all_paths if fnmatch.fnmatch(p, f"*{pattern}*")]
        for path in matches:
            count = conn.execute(
                "DELETE FROM knowledge_base WHERE file_path = ?",
                (path,),
            ).rowcount
            deleted += count
            print(f"  [delete] {path}: {count} chunks removed")
    elif target.is_dir():
        # Delete all files under directory
        prefix = str(target) + "/"
        rows = conn.execute(
            "SELECT DISTINCT file_path FROM knowledge_base WHERE file_path LIKE ?",
            (prefix + "%",),
        ).fetchall()
        for row in rows:
            count = conn.execute(
                "DELETE FROM knowledge_base WHERE file_path = ?",
                (row["file_path"],),
            ).rowcount
            deleted += count
            print(f"  [delete] {row['file_path']}: {count} chunks removed")
    else:
        # Single file deletion
        count = conn.execute(
            "DELETE FROM knowledge_base WHERE file_path = ?",
            (str(target),),
        ).rowcount
        deleted = count

    conn.commit()
    conn.close()

    print(f"[delete] Total {deleted} chunks deleted for {target}")


if __name__ == "__main__":
    main()

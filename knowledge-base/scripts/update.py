#!/usr/bin/env python3
"""Update: DELETE old chunks for file_path → re-INSERT with new content."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.db_client import get_connection
from core.chunker import chunk_file
from core.embedder import embed_texts
import json


def main():
    if len(sys.argv) < 2:
        print("[update] Usage: update.py <file_path>")
        sys.exit(1)

    file_path = Path(sys.argv[1]).resolve()

    if not file_path.exists():
        print(f"[update] ERROR: file not found: {file_path}")
        sys.exit(1)

    conn = get_connection()

    # Delete old chunks for this file
    deleted = conn.execute(
        "DELETE FROM knowledge_base WHERE file_path = ?",
        (str(file_path),),
    ).rowcount
    conn.commit()

    print(f"[update] Deleted {deleted} old chunks for {file_path}")

    # Re-chunk and re-embed
    chunks = chunk_file(str(file_path))
    if not chunks:
        print(f"[update] No chunks extracted. Nothing to insert.")
        conn.close()
        return

    contents = [c["content"] for c in chunks]
    embeddings = embed_texts(contents)

    inserted = 0
    for chunk, emb in zip(chunks, embeddings):
        try:
            vec_str = json.dumps(emb)
            conn.execute(
                "INSERT INTO knowledge_base (file_path, chunk_index, content, embedding, metadata) "
                "VALUES (?, ?, ?, ?, ?)",
                (
                    str(file_path),
                    chunk["index"],
                    chunk["content"],
                    vec_str,
                    json.dumps({"kind": chunk["kind"], "start_byte": chunk["start_byte"]}),
                ),
            )
            inserted += 1
        except Exception as e:
            print(f"[update] WARNING: chunk {chunk['index']} failed: {e}")

    conn.commit()
    conn.close()

    print(f"[update] Inserted {inserted} new chunks for {file_path}")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""Create: Parse file → chunk → embed → INSERT into knowledge_base."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.db_client import get_connection
from core.chunker import chunk_file
from core.embedder import embed_texts


def main():
    if len(sys.argv) < 2:
        print("[create] Usage: create.py <file_path> [--force]")
        sys.exit(1)

    file_path = Path(sys.argv[1]).resolve()
    force = "--force" in sys.argv

    if not file_path.exists():
        print(f"[create] ERROR: file not found: {file_path}")
        sys.exit(1)

    # Chunk
    chunks = chunk_file(str(file_path))
    if not chunks:
        print(f"[create] No chunks extracted from {file_path}")
        sys.exit(0)

    # Embed
    contents = [c["content"] for c in chunks]
    embeddings = embed_texts(contents)

    # Insert
    conn = get_connection()
    upsert = "OR REPLACE" if force else ""
    inserted = 0
    for chunk, emb in zip(chunks, embeddings):
        try:
            # sqlite-vec expects vector as JSON array string
            vec_str = json.dumps(emb)
            conn.execute(
                f"INSERT {upsert} INTO knowledge_base (file_path, chunk_index, content, embedding, metadata) "
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
            print(f"[create] WARNING: chunk {chunk['index']} failed: {e}")

    conn.commit()
    conn.close()

    print(f"[create] Inserted {inserted} chunks from {file_path}")
    for chunk in chunks[:3]:
        print(f"  - chunk#{chunk['index']} ({chunk['kind']}): {chunk['content'][:80]}...")
    if len(chunks) > 3:
        print(f"  ... and {len(chunks) - 3} more")


if __name__ == "__main__":
    main()

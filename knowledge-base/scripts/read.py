#!/usr/bin/env python3
"""Read: Hybrid search (vector cosine + FTS5) → top-k results."""
import sys
import json
import math
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from core.db_client import get_connection
from core.embedder import embed_single


DEFAULT_TOP_K = 5


def cosine_similarity(query_vec, doc_vec):
    """Compute cosine similarity between two vectors."""
    dot = sum(a * b for a, b in zip(query_vec, doc_vec))
    return dot  # vectors are pre-normalized, so dot = cosine


def main():
    if len(sys.argv) < 2:
        print("[read] Usage: read.py <query> [--top-k N] [--fuzzy]")
        sys.exit(1)

    query = " ".join(sys.argv[1:])
    # Parse optional flags
    top_k = DEFAULT_TOP_K
    fuzzy = False
    for arg in sys.argv[2:]:
        if arg == "--fuzzy":
            fuzzy = True
        elif arg == "--top-k" and len(sys.argv) > sys.argv.index(arg) + 1:
            top_k = int(sys.argv[sys.argv.index(arg) + 1])

    # Embed query
    query_emb = embed_single(query)
    query_vec_str = json.dumps(query_emb)

    conn = get_connection()

    # Vector search (sqlite-vec)
    vec_results = conn.execute(
        f"""
        SELECT id, file_path, chunk_index, content, metadata,
               vec_distance_l2(embedding, '{query_vec_str}') as distance
        FROM knowledge_base
        ORDER BY distance ASC
        LIMIT {top_k * 2}
        """
    ).fetchall()

    # FTS5 search (join with main table for metadata)
    # Sanitize: replace hyphens with spaces (FTS5 treats - as operator)
    sanitized = query.replace("-", " ").replace("_", " ")
    search_term = sanitized if not fuzzy else sanitized + "*"
    fts_results = conn.execute(
        f"""
        SELECT kb.id, kb.file_path, kb.chunk_index, kb.content, kb.metadata, knowledge_fts.rank
        FROM knowledge_fts
        JOIN knowledge_base kb ON kb.id = knowledge_fts.rowid
        WHERE knowledge_fts MATCH ?
        ORDER BY rank ASC
        LIMIT {top_k * 2}
        """,
        (search_term,),
    ).fetchall()

    # Merge: rank by combined score (convert rows to dicts)
    vec_map = {row["id"]: dict(row) for row in vec_results}
    fts_map = {row["id"]: dict(row) for row in fts_results}

    all_ids = set(vec_map) | set(fts_map)
    scored = []
    for row_id in all_ids:
        vec_rank = vec_map[row_id].get("distance", float("inf")) if row_id in vec_map else float("inf")
        fts_rank = fts_map[row_id].get("rank", float("inf")) if row_id in fts_map else float("inf")

        # Normalize: lower = better for both
        score = (vec_rank * 0.6) + (fts_rank * 0.4) if math.isfinite(vec_rank) and math.isfinite(fts_rank) else min(vec_rank, fts_rank)
        scored.append((score, row_id))

    scored.sort()
    top = scored[:top_k]

    print(f"[read] Query: \"{query}\"")
    print(f"[read] Found {len(top)} results (from {len(all_ids)} candidates)")
    print("-" * 60)

    for score, row_id in top:
        row = vec_map.get(row_id) or fts_map.get(row_id)
        print(f"  File: {row['file_path']} (chunk#{row['chunk_index']})")
        print(f"  Content: {row['content'][:200]}")
        print(f"  Score: {score:.4f}")
        print("-" * 60)

    conn.close()


if __name__ == "__main__":
    main()

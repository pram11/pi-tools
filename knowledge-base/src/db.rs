use rusqlite::{ffi::sqlite3_auto_extension, Connection, OpenFlags, Result};
use sqlite_vec::sqlite3_vec_init;
use std::path::PathBuf;
use std::sync::Once;

static INIT: Once = Once::new();

fn register_sqlite_vec() {
    INIT.call_once(|| {
        unsafe {
            sqlite3_auto_extension(Some(std::mem::transmute(
                sqlite3_vec_init as *const (),
            )));
        }
    });
}

pub fn get_connection() -> Result<Connection> {
    register_sqlite_vec();
    let path = db_path();
    let parent = path.parent().unwrap();
    if !parent.exists() {
        std::fs::create_dir_all(parent).expect("Failed to create DB dir");
    }
    Connection::open_with_flags(
        &path,
        OpenFlags::SQLITE_OPEN_READ_WRITE | OpenFlags::SQLITE_OPEN_CREATE,
    )
}

fn db_path() -> PathBuf {
    dirs::home_dir().unwrap().join(".pi/agent-memory/knowledge.db")
}

pub fn init_schema(conn: &Connection) -> Result<()> {
    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS knowledge_base (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_path TEXT NOT NULL,
            chunk_index INTEGER NOT NULL,
            content TEXT NOT NULL,
            embedding FLOAT[768],
            metadata TEXT,
            UNIQUE(file_path, chunk_index)
        );",
    )?;
    conn.execute_batch(
        "CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(content, content=knowledge_base, content_rowid=id);",
    )?;
    conn.execute_batch(
        "CREATE TRIGGER IF NOT EXISTS kb_ai AFTER INSERT ON knowledge_base BEGIN
            INSERT INTO knowledge_fts(rowid, content) VALUES (new.id, new.content);
        END;",
    )?;
    conn.execute_batch(
        "CREATE TRIGGER IF NOT EXISTS kb_ad AFTER DELETE ON knowledge_base BEGIN
            INSERT INTO knowledge_fts(knowledge_fts, rowid, content) VALUES ('delete', old.id, old.content);
        END;",
    )?;
    conn.execute_batch(
        "CREATE TRIGGER IF NOT EXISTS kb_au AFTER UPDATE ON knowledge_base BEGIN
            INSERT INTO knowledge_fts(knowledge_fts, rowid, content) VALUES ('delete', old.id, old.content);
            INSERT INTO knowledge_fts(rowid, content) VALUES (new.id, new.content);
        END;",
    )?;
    Ok(())
}

/// Convert f32 vector to sqlite-vec blob (little-endian)
pub fn embedding_to_blob(emb: &[f32]) -> Vec<u8> {
    let mut blob = Vec::with_capacity(emb.len() * 4);
    for &v in emb {
        blob.extend_from_slice(&v.to_le_bytes());
    }
    blob
}

/// Compute cosine similarity between two f32 vectors
fn cosine_sim(a: &[f32], b: &[f32]) -> f32 {
    let mut dot = 0.0f32;
    let mut na = 0.0f32;
    let mut nb = 0.0f32;
    for i in 0..a.len().min(b.len()) {
        dot += a[i] * b[i];
        na += a[i] * a[i];
        nb += b[i] * b[i];
    }
    let denom = (na * nb).sqrt();
    if denom > 0.0 { dot / denom } else { 0.0 }
}

/// Deserialize embedding blob back to f32 slice
fn blob_to_f32(blob: &[u8]) -> Vec<f32> {
    if blob.len() % 4 != 0 { return Vec::new(); }
    let n = blob.len() / 4;
    let mut out = Vec::with_capacity(n);
    for i in 0..n {
        let bytes: [u8; 4] = [blob[i*4], blob[i*4+1], blob[i*4+2], blob[i*4+3]];
        out.push(f32::from_le_bytes(bytes));
    }
    out
}

/// Hybrid search: vector similarity (pure Rust) + FTS5
pub fn hybrid_search(
    conn: &Connection,
    query_embedding: &[u8],
    query_text: &str,
    top_k: usize,
    use_fuzzy: bool,
) -> Result<Vec<(i64, String, String, f64)>> {
    let query_vec = blob_to_f32(query_embedding);

    // Fetch all rows with embeddings
    let rows: Vec<(i64, String, String, Vec<u8>)> = conn
        .prepare("SELECT id, file_path, content, embedding FROM knowledge_base WHERE embedding IS NOT NULL AND embedding != X''")?
        .query_map([], |r| {
            Ok((r.get(0)?, r.get(1)?, r.get(2)?, r.get::<_, Vec<u8>>(3)?))
        })?
        .collect::<Result<Vec<_>, _>>()?;

    // Compute cosine similarity
    let mut scored: Vec<(i64, String, String, f64)> = rows
        .into_iter()
        .filter_map(|(id, fp, content, emb)| {
            let emb_vec = blob_to_f32(&emb);
            let sim = cosine_sim(&query_vec, &emb_vec) as f64;
            if emb_vec.is_empty() { None } else { Some((id, fp, content, sim)) }
        })
        .collect();
    // Sort by similarity desc
    scored.sort_by(|a, b| b.3.partial_cmp(&a.3).unwrap_or(std::cmp::Ordering::Equal));
    scored.truncate(top_k);

    if !use_fuzzy {
        return Ok(scored);
    }

    // FTS5 search
    let fts_ids: Vec<i64> = conn
        .prepare("SELECT id FROM knowledge_base WHERE rowid IN (SELECT rowid FROM knowledge_fts WHERE knowledge_fts MATCH ?)")?
        .query_map([query_text], |r| r.get(0))?
        .collect::<Result<Vec<_>, _>>()?;

    let scored_ids: std::collections::HashSet<_> = scored.iter().map(|(id, _, _, _)| *id).collect();
    for id in fts_ids {
        if !scored_ids.contains(&id) {
            if let Ok(row) = conn.query_row(
                "SELECT file_path, content FROM knowledge_base WHERE id = ?",
                [id],
                |r| Ok((r.get(0)?, r.get(1)?)),
            ) {
                scored.push((id, row.0, row.1, 0.0));
            }
        }
    }
    scored.truncate(top_k);
    Ok(scored)
}

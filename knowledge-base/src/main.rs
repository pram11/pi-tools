mod chunker;
mod cli;
mod db;
mod embedder;

use clap::Parser;
use cli::{Command, App};
use db::{embedding_to_blob, get_connection, hybrid_search, init_schema};
use std::path::PathBuf;
use std::process;

const MODEL_PATH: &str = "/root/.pi/agent/skills/knowledge-base/models/nomic-embed-text-v1.5.Q4_K_M.gguf";

fn main() {
    let app = App::parse();
    let res = match app.command {
        Command::Init => run_init(),
        Command::Create { file_path, force } => run_create(file_path, force),
        Command::Search { query, top_k, fuzzy } => run_search(query, Some(top_k), fuzzy),
        Command::Update { file_path } => run_update(file_path),
        Command::Delete { target, pattern } => run_delete(target, pattern),
    };
    if let Err(e) = res {
        eprintln!("[kb] Error: {}", e);
        process::exit(1);
    }
}

fn run_init() -> Result<(), Box<dyn std::error::Error>> {
    let conn = get_connection()?;
    init_schema(&conn)?;
    println!("[kb] DB initialized");
    Ok(())
}

fn run_create(file_path: PathBuf, force: bool) -> Result<(), Box<dyn std::error::Error>> {
    let canonical = file_path.canonicalize().unwrap_or(file_path.clone());
    let fp = canonical.to_string_lossy().to_string();

    let chunks = chunker::chunk_file(&canonical);
    if chunks.is_empty() {
        println!("[kb] No chunks from: {}", file_path.display());
        return Ok(());
    }

    let embeddings: Vec<Vec<f32>> = chunks
        .iter()
        .map(|c| {
            embedder::embed_text(std::path::Path::new(MODEL_PATH), &c.content)
                .unwrap_or_else(|_| vec![0.0; embedder::EMBEDDING_DIM])
        })
        .collect();

    let mut conn = get_connection()?;
    let tx = conn.transaction()?;

    if force {
        tx.execute("DELETE FROM knowledge_base WHERE file_path = ?", [&fp])?;
    }

    for (i, chunk) in chunks.iter().enumerate() {
        let blob = embedding_to_blob(&embeddings[i]);
        let meta = serde_json::json!({"kind": &chunk.kind, "start_byte": chunk.start_byte});
        tx.execute(
            "INSERT OR IGNORE INTO knowledge_base (file_path, chunk_index, content, embedding, metadata) VALUES (?, ?, ?, ?, ?)",
            rusqlite::params![fp.clone(), chunk.index, chunk.content.clone(), blob, meta.to_string()],
        )?;
    }
    tx.commit()?;
    println!("[kb] Indexed {} chunks from {}", chunks.len(), file_path.display());
    Ok(())
}

fn run_search(query: String, top_k: Option<usize>, fuzzy: bool) -> Result<(), Box<dyn std::error::Error>> {
    let top_k = top_k.unwrap_or(5);
    let query_emb = embedder::embed_text(std::path::Path::new(MODEL_PATH), &query)?;
    let query_blob = embedding_to_blob(&query_emb);

    let conn = get_connection()?;
    let results = hybrid_search(&conn, &query_blob, &query, top_k, fuzzy)?;

    if results.is_empty() {
        println!("[kb] No results for: {}", query);
        return Ok(());
    }

    println!("[kb] Found {} result(s) for: '{}'", results.len(), query);
    for (i, (id, file_path, content, score)) in results.iter().enumerate() {
        println!("  [{}] id={} file={}", i + 1, id, file_path);
        let preview: String = content.chars().take(120).collect();
        println!("      {}...", preview);
        println!("      score={:.4}", score);
    }
    Ok(())
}

fn run_update(file_path: PathBuf) -> Result<(), Box<dyn std::error::Error>> {
    let canonical = file_path.canonicalize().unwrap_or(file_path.clone());
    let fp = canonical.to_string_lossy().to_string();
    let conn = get_connection()?;
    conn.execute("DELETE FROM knowledge_base WHERE file_path = ?", [&fp])?;
    run_create(canonical, false)
}

fn run_delete(target: PathBuf, pattern: Option<String>) -> Result<(), Box<dyn std::error::Error>> {
    let conn = get_connection()?;
    let canonical = target.canonicalize().unwrap_or(target.clone());
    let fp = canonical.to_string_lossy().to_string();

    if canonical.is_dir() {
        let prefix = format!("{}%", fp);
        conn.execute("DELETE FROM knowledge_base WHERE file_path LIKE ?", [&prefix])?;
    } else if let Some(pat) = &pattern {
        conn.execute("DELETE FROM knowledge_base WHERE file_path GLOB ?", [&pat])?;
    } else {
        conn.execute("DELETE FROM knowledge_base WHERE file_path = ?", [&fp])?;
    }

    let rows = conn.query_row("SELECT changes()", [], |r| r.get::<_, i64>(0))?;
    println!("[kb] Deleted {} row(s)", rows);
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_embedding_blob_size() {
        let emb = vec![0.1f32; embedder::EMBEDDING_DIM];
        let blob = embedding_to_blob(&emb);
        assert_eq!(blob.len(), embedder::EMBEDDING_DIM * 4);
    }
}

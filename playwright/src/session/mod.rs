use std::path::PathBuf;
use std::time::SystemTime;
use anyhow::Result;
use serde::{Deserialize, Serialize};
use rusqlite::{Connection, params};

pub mod db;

const SESSIONS_DIR: &str = ".sessions";
const DB_FILE: &str = "state.db";
const STORAGE_FILE: &str = "storage.json";

#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct Session {
    pub url: String,
    pub title: String,
    pub cookies: serde_json::Value,
    pub updated_at: String,
}

pub fn sessions_dir() -> PathBuf {
    let dir = PathBuf::from(SESSIONS_DIR);
    std::fs::create_dir_all(&dir).ok();
    dir
}

pub fn db_path() -> PathBuf {
    sessions_dir().join(DB_FILE)
}

pub fn storage_path() -> PathBuf {
    sessions_dir().join(STORAGE_FILE)
}

pub fn init_db() -> Result<Connection> {
    let path = db_path();
    let conn = Connection::open(&path)?;
    conn.execute_batch(
        "CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            url TEXT,
            title TEXT,
            cookies TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )",
    )?;
    Ok(conn)
}

pub fn session_active() -> bool {
    let conn = match init_db() {
        Ok(c) => c,
        Err(_) => return false,
    };
    let mut stmt = conn.prepare("SELECT 1 FROM sessions WHERE id = 1").unwrap();
    stmt.query_row([], |_| Ok(())).unwrap_or(false)
}

pub fn load_session() -> Option<Session> {
    let conn = init_db().ok()?;
    let mut stmt = conn.prepare("SELECT url, title, cookies FROM sessions WHERE id = 1").ok()?;
    stmt.query_row([], |row| {
        Ok(Session {
            url: row.get(0)?,
            title: row.get(1)?,
            cookies: serde_json::Value::String(row.get(2)?),
            updated_at: SystemTime::now().to_string(),
        })
    }).ok()
}

pub fn save_session(url: &str, title: &str, cookies: &str) -> Result<()> {
    let conn = init_db()?;
    conn.execute(
        "INSERT INTO sessions (id, url, title, cookies) VALUES (1, ?, ?, ?)
         ON CONFLICT(id) DO UPDATE SET url=excluded.url, title=excluded.title, cookies=excluded.cookies",
        params![url, title, cookies],
    )?;
    Ok(())
}

pub fn clear_session() -> Result<()> {
    let conn = init_db()?;
    conn.execute("DELETE FROM sessions WHERE id = 1", [])?;
    let sp = storage_path();
    if sp.exists() {
        std::fs::remove_file(&sp).ok();
    }
    Ok(())
}

/// Returns path to storage.json if it exists.
pub fn storage_state_path() -> Option<PathBuf> {
    let p = storage_path();
    if p.exists() { Some(p) } else { None }
}

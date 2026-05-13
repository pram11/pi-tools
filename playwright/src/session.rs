use anyhow::Result;
use std::path::PathBuf;
use std::fs;

const SESSION_DIR: &str = ".playwright_sessions";
const SESSION_FILE: &str = "session.json";
const STORAGE_FILE: &str = "storage.json";
const ACTIVE_FILE: &str = "active.flag";

pub fn session_dir() -> PathBuf {
    let d = PathBuf::from(SESSION_DIR);
    fs::create_dir_all(&d).ok();
    d
}

pub fn storage_path() -> PathBuf {
    session_dir().join(STORAGE_FILE)
}

pub fn storage_state_path() -> Option<PathBuf> {
    let p = storage_path();
    if p.exists() { Some(p) } else { None }
}

pub fn session_active() -> bool {
    session_dir().join(ACTIVE_FILE).exists()
}

pub fn save_session(url: &str, title: &str, cookies_json: &str) -> Result<()> {
    let data = serde_json::json!({ "url": url, "title": title, "cookies": cookies_json });
    fs::write(session_dir().join(SESSION_FILE), serde_json::to_string(&data)?)?;
    fs::write(session_dir().join(ACTIVE_FILE), "1")?;
    Ok(())
}

pub fn clear_session() -> Result<()> {
    let d = session_dir();
    if d.join(SESSION_FILE).try_exists().unwrap_or(false) { fs::remove_file(d.join(SESSION_FILE)).ok(); }
    if d.join(ACTIVE_FILE).try_exists().unwrap_or(false) { fs::remove_file(d.join(ACTIVE_FILE)).ok(); }
    if d.join(STORAGE_FILE).try_exists().unwrap_or(false) { fs::remove_file(d.join(STORAGE_FILE)).ok(); }
    Ok(())
}

pub fn load_session() -> Option<SessionData> {
    let path = session_dir().join(SESSION_FILE);
    let content = fs::read_to_string(&path).ok()?;
    let data: SessionData = serde_json::from_str(&content).ok()?;
    Some(data)
}

#[derive(Debug, serde::Deserialize, serde::Serialize)]
pub struct SessionData {
    pub url: String,
    pub title: String,
    #[serde(default)]
    pub cookies: String,
}

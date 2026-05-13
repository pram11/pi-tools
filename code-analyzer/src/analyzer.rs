//! Analyzer trait — Strategy Pattern contract.

use std::path::Path;

use crate::schema::Finding;

/// Canonical error type.
#[derive(Debug, thiserror::Error)]
#[allow(dead_code)]
pub enum Error {
    #[error("io: {0}")]
    Io(#[from] std::io::Error),
    #[error("other: {0}")]
    Other(String),
}

/// Language analyzer interface.
pub trait Analyzer: Send + Sync {
    fn languages(&self) -> &[&str];
    fn analyze(&self, target: &Path) -> Result<Vec<Finding>, Error>;
}

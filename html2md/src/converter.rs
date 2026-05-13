use thiserror::Error;

#[derive(Debug, Error)]
pub enum ConverterError {
    #[error("unknown backend: {0}")]
    UnknownBackend(String),
    #[error("sanitization failed: {0}")]
    Sanitization(String),
    #[error("conversion failed: {0}")]
    Conversion(String),
    #[error("I/O error: {0}")]
    Io(#[from] std::io::Error),
}

pub type Result<T> = std::result::Result<T, ConverterError>;

pub trait Converter: std::fmt::Debug + Send + Sync {
    /// Human-readable backend name.
    fn name(&self) -> &str;

    /// Convert raw HTML string → Markdown string.
    fn convert(&self, html: &str) -> Result<String>;
}

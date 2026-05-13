use url::Url;
use anyhow::{Result, Context};

/// Extract origin (scheme + host + port) from URL string.
pub fn extract_origin(url: &str) -> Result<String> {
    let parsed = Url::parse(url).context("Invalid URL")?;
    Ok(parsed.origin().ascii_serialization())
}

/// Retry a fallible async closure with exponential backoff.
pub async fn retry<F, Fut, T>(
    max_retries: usize,
    mut f: F,
) -> Result<T>
where
    F: FnMut() -> Fut,
    Fut: std::future::Future<Output = Result<T>>,
{
    let mut last_err = None;
    for attempt in 1..=max_retries {
        match f().await {
            Ok(val) => return Ok(val),
            Err(e) => {
                let msg = e.to_string().to_lowercase();
                if msg.contains("timeout") || msg.contains("crash") || msg.contains("closed") {
                    if attempt < max_retries {
                        eprintln!("[recovery] Attempt {attempt} failed: {e}");
                        last_err = Some(e);
                        tokio::time::sleep(std::time::Duration::from_millis(500 * attempt as u64)).await;
                        continue;
                    }
                }
                return Err(e);
            }
        }
    }
    Err(last_err.unwrap_or_else(|| anyhow::anyhow!("Navigation failed after {max_retries} attempt(s)")))
}

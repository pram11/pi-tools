use std::time::Duration;

pub async fn retry<F, Fut, T>(max_retries: usize, f: F) -> Result<T, anyhow::Error>
where
    F: Fn() -> Fut,
    Fut: std::future::Future<Output = Result<T, anyhow::Error>>,
{
    let mut last_err = anyhow::anyhow!("No attempts made");
    for i in 0..=max_retries {
        match f().await {
            Ok(v) => return Ok(v),
            Err(e) => {
                last_err = e;
                if i < max_retries {
                    tokio::time::sleep(Duration::from_millis(100 * (1 << i))).await;
                }
            }
        }
    }
    Err(last_err)
}

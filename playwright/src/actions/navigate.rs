use anyhow::Result;
use playwright::Page;
use crate::actions::CliArgs;
use crate::utils::retry;

pub async fn action_navigate(page: &Page, args: &CliArgs) -> Result<()> {
    let url = args.url.clone().ok_or_else(|| anyhow::anyhow!("No URL provided"))?;
    retry(args.retries, || async {
        page.goto(&url)
            .wait_until(playwright::types::WaitUntil::DomContentLoaded)
            .timeout(args.timeout)
            .await?;
        Ok(())
    }).await?;
    println!("[navigate] Loaded: {}", page.url().await);
    Ok(())
}

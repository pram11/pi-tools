use anyhow::Result;
use playwright::api::page::Page;
use crate::actions::CliArgs;
use crate::utils::retry;

pub async fn action_navigate(page: &Page, args: &CliArgs) -> Result<()> {
    let url = args.url.clone().ok_or_else(|| anyhow::anyhow!("No URL provided"))?;
    retry(args.retries, || async {
        page.goto_builder(&url)
            .timeout(args.timeout as f64)
            .goto().await?;
        Ok(())
    }).await?;
    println!("[navigate] Loaded: {}", page.url()?);
    Ok(())
}

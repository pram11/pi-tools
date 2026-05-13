use anyhow::Result;
use playwright::Page;
use std::path::Path;
use crate::actions::CliArgs;

pub async fn action_upload_detect(page: &Page, _args: &CliArgs) -> Result<()> {
    let js = r#"() => {
        const inputs = document.querySelectorAll('input[type="file"]');
        return Array.from(inputs).map(el => ({
            name: el.name || '', id: el.id || '', accept: el.accept || '', multiple: el.hasAttribute('multiple')
        }));
    }"#;
    let result: serde_json::Value = page.evaluate(js).await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

pub async fn action_upload(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let paths_str = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No file paths"))?;
    let paths: Vec<&str> = paths_str.split(',').map(|s| s.trim()).collect();

    for p in &paths {
        if !Path::new(*p).exists() {
            anyhow::bail!("Upload file not found: {p}");
        }
    }

    let input = page.locator(sel);
    input.wait_for().timeout(5000).await?;
    input.set_input_files(&paths).await?;

    let result: serde_json::Value = page.evaluate(&format!(
        r#"(sel) => {{ const el = document.querySelector(sel); return el ? Array.from(el.files).map(f => f.name) : []; }}"#
    )).await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

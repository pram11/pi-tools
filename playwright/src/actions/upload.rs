use anyhow::Result;
use playwright::api::page::Page;
use crate::actions::CliArgs;

pub async fn action_upload(page: &Page, args: &CliArgs) -> Result<()> {
    let _sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let file = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No file path"))?;
    let abs_path = std::path::Path::new(file);
    if !abs_path.exists() {
        anyhow::bail!("File not found: {file}");
    }
    let path_str = abs_path.to_str().unwrap_or(file);
    let _path_json = serde_json::to_string(path_str)?;

    let js = format!(
        r#"(sel, file) => {{
            const el = document.querySelector(sel);
            if (!el || el.tagName.toLowerCase() !== 'input' || el.type !== 'file') return false;
            // Note: actual file upload requires playwright's setInputFiles API
            // This sets the path for later use
            el.dataset.file = file;
            return true;
        }}"#,
    );
    let set: bool = page.eval::<bool>(&js).await.unwrap_or(false);
    if set {
        // Use JS to read file and create blob
        let file_data = std::fs::read_to_string(file).unwrap_or_default();
        let _data_json = serde_json::to_string(&file_data)?;
        let js2 = format!(
            r#"(sel, data) => {{
                const el = document.querySelector(sel);
                if (!el) return false;
                const blob = new Blob([data], {{type: 'text/plain'}});
                const dt = new DataTransfer();
                const f = new File([blob], 'uploaded.txt', {{type: 'text/plain'}});
                dt.items.add(f);
                el.files = dt.files;
                el.dispatchEvent(new Event('change', {{bubbles: true}}));
                return true;
            }}"#,
        );
        let uploaded: bool = page.eval::<bool>(&js2).await.unwrap_or(false);
        println!("{{\"uploaded\": {}}}", uploaded);
    } else {
        println!("{{\"uploaded\": false}}");
    }
    Ok(())
}

pub async fn action_upload_detect(page: &Page, _args: &CliArgs) -> Result<()> {
    let js = r#"() => {
        const nodes = document.querySelectorAll('input[type=file]');
        return Array.from(nodes).map(n => ({
            tag: n.tagName.toLowerCase(),
            name: n.name || '',
            id: n.id || '',
            accept: n.accept || '',
            multiple: n.multiple,
        }));
    }"#;
    let result: serde_json::Value = page.eval(js).await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

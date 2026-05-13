use anyhow::Result;
use playwright::api::page::Page;
use crate::actions::CliArgs;

fn js_shadow_query(sel: &str) -> String {
    let parts: Vec<&str> = sel.split('/').collect();
    let mut js = "let el = document;".to_string();
    for p in parts {
        let trimmed = p.trim();
        if trimmed.is_empty() { continue; }
        if trimmed.starts_with(">>>") || trimmed.starts_with(">>") {
            js.push_str("el = el.shadowRoot;");
        } else {
            let escaped = serde_json::to_string(trimmed).unwrap_or_default();
            js.push_str(&format!("el = el.querySelector({});", escaped));
        }
    }
    format!("(() => {{ {}; return el; }})()", js)
}

pub async fn action_shadow_detect(page: &Page, _args: &CliArgs) -> Result<()> {
    let js = r#"() => {
        const roots = [];
        const els = document.querySelectorAll('*');
        for (const el of els) {
            if (el.shadowRoot) {
                roots.push({
                    tag: el.tagName.toLowerCase(),
                    id: el.id || '',
                    hostSelector: el.id ? `#${el.id}` : el.tagName.toLowerCase()
                });
            }
        }
        return roots;
    }"#;
    let result: serde_json::Value = page.eval(js).await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

pub async fn action_shadow_query(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let js = format!("(() => {{ const el = ({}); return el ? el.textContent.trim() : null; }})()", js_shadow_query(sel));
    let text: Option<String> = page.eval(&js).await.unwrap_or(None);
    println!("{{\"text\": {:?}}}", text);
    Ok(())
}

pub async fn action_shadow_click(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let js = format!("(() => {{ const el = ({}); if (el) el.click(); return !!el; }})()", js_shadow_query(sel));
    let clicked: bool = page.eval::<bool>(&js).await.unwrap_or(false);
    println!("{{\"clicked\": {}}}", clicked);
    Ok(())
}

pub async fn action_shadow_fill(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let val = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No value"))?;
    let val_json = serde_json::to_string(val)?;
    let js = format!("(() => {{ const el = ({}); if (el) {{ el.value = {}; el.dispatchEvent(new Event('input', {{bubbles:true}})); return true; }} return false; }})()", js_shadow_query(sel), val_json);
    let filled: bool = page.eval::<bool>(&js).await.unwrap_or(false);
    println!("{{\"filled\": {}}}", filled);
    Ok(())
}

pub async fn action_shadow_extract(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let child = args.value.as_deref().unwrap_or("*");
    let child_json = serde_json::to_string(child)?;
    let js = format!("(() => {{ const el = ({}); return el ? Array.from(el.querySelectorAll({})).map(e => e.textContent.trim()) : []; }})()", js_shadow_query(sel), child_json);
    let result: serde_json::Value = page.eval(&js).await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

pub async fn action_shadow_pierce(page: &Page, args: &CliArgs) -> Result<()> {
    let sel = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No selector"))?;
    let js = format!("(() => {{ const el = ({}); return el ? el.textContent.trim() : null; }})()", js_shadow_query(sel));
    let text: Option<String> = page.eval(&js).await.unwrap_or(None);
    println!("{{\"text\": {:?}}}", text);
    Ok(())
}

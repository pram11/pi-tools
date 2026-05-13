use anyhow::Result;
use playwright::Page;
use crate::actions::CliArgs;

pub async fn action_shadow_detect(page: &Page, _args: &CliArgs) -> Result<()> {
    let js = r#"() => {
        const all = document.querySelectorAll('*');
        return Array.from(all).filter(el => el.shadowRoot)
            .map(el => ({ tag: el.tagName.toLowerCase(), id: el.id || '', childCount: el.shadowRoot.children.length }));
    }"#;
    let result: serde_json::Value = page.evaluate(js).await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

pub async fn action_shadow_query(page: &Page, args: &CliArgs) -> Result<()> {
    let host = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No host selector"))?;
    let inner = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No inner selector"))?;
    let js = format!(r#"
        (host, inner) => {{
            const el = document.querySelector(host);
            if (!el || !el.shadowRoot) return null;
            const found = el.shadowRoot.querySelector(inner);
            return found ? found.textContent.trim() : null;
        }}
    "#);
    let result: Option<String> = page.evaluate(&js).await?;
    if let Some(text) = result {
        println!("{text}");
    }
    Ok(())
}

pub async fn action_shadow_click(page: &Page, args: &CliArgs) -> Result<()> {
    let host = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No host selector"))?;
    let inner = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No inner selector"))?;
    let js = format!(r#"
        (host, inner) => {{
            const el = document.querySelector(host);
            if (!el || !el.shadowRoot) throw new Error('Shadow host not found');
            const found = el.shadowRoot.querySelector(inner);
            if (!found) throw new Error('Inner element not found');
            found.click();
        }}
    "#);
    page.evaluate(&js).await?;
    println!("[shadow] Clicked: {host} >> {inner}");
    Ok(())
}

pub async fn action_shadow_fill(page: &Page, args: &CliArgs) -> Result<()> {
    let host = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No host selector"))?;
    let inner = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No inner selector"))?;
    let text = args.output.as_deref().unwrap_or("");
    let js = format!(r#"
        (host, inner, text) => {{
            const el = document.querySelector(host);
            if (!el || !el.shadowRoot) throw new Error('Shadow host not found');
            const found = el.shadowRoot.querySelector(inner);
            if (!found) throw new Error('Inner element not found');
            found.value = text;
            found.dispatchEvent(new Event('input', {{bubbles: true}}));
            found.dispatchEvent(new Event('change', {{bubbles: true}}));
        }}
    "#);
    page.evaluate(&js).await?;
    println!("[shadow] Filled: {host} >> {inner}");
    Ok(())
}

pub async fn action_shadow_extract(page: &Page, args: &CliArgs) -> Result<()> {
    let host = args.selector.as_deref().ok_or_else(|| anyhow::anyhow!("No host selector"))?;
    let inner = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No inner selector"))?;
    let js = format!(r#"
        (host, inner) => {{
            const hosts = document.querySelectorAll(host);
            const results = [];
            for (const h of hosts) {{
                const shadow = h.shadowRoot;
                if (!shadow) continue;
                const el = shadow.querySelector(inner);
                if (el) results.push(el.textContent.trim());
            }}
            return results;
        }}
    "#);
    let result: serde_json::Value = page.evaluate(&js).await?;
    println!("{}", serde_json::to_string_pretty(&result)?);
    Ok(())
}

pub async fn action_shadow_pierce(page: &Page, args: &CliArgs) -> Result<()> {
    let chain = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No chain"))?;
    let js = r#"
        (selectors) => {
            let el = document.querySelector(selectors[0]);
            if (!el) return null;
            for (let i = 1; i < selectors.length; i++) {
                const shadow = el.shadowRoot;
                if (!shadow) throw new Error('No shadow root at segment ' + i);
                el = shadow.querySelector(selectors[i]);
                if (!el) throw new Error('Element not found at segment ' + i);
            }
            return el.textContent.trim();
        }
    "#;
    let parts: Vec<&str> = chain.split(">>").map(|s| s.trim()).collect();
    let parts_json = serde_json::to_value(&parts)?;
    let result: Option<String> = page.evaluate(&js).await?;
    if let Some(text) = result {
        println!("{text}");
    }
    Ok(())
}

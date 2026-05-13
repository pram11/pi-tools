use anyhow::Result;
use playwright::api::page::Page;
use playwright::api::browser_context::BrowserContext;
use crate::actions::CliArgs;

pub async fn action_auth_inject(page: &Page, context: &BrowserContext, args: &CliArgs) -> Result<()> {
    let auth_data: serde_json::Value = serde_json::from_str(
        args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No auth JSON"))?
    )?;

    // Inject cookies via JS (Cookie struct not public in 0.0.20)
    if let Some(cookies) = auth_data.get("cookies") {
        let cookies_json = serde_json::to_string(cookies)?;
        let js = format!(r#"
            (() => {{
                const cookies = {cookies_json};
                for (const c of cookies) {{
                    const parts = [`${{c.name}}=${{c.value}}`];
                    if (c.domain) parts.push(`domain=${{c.domain}}`);
                    if (c.path) parts.push(`path=${{c.path}}`);
                    if (c.expires) parts.push(`expires=${{new Date(c.expires * 1000).toUTCString()}}`);
                    if (c.secure) parts.push('secure');
                    if (c.httpOnly) parts.push('HttpOnly');
                    document.cookie = parts.join('; ');
                }}
            }})()
        "#);
        page.eval::<()>(&js).await?;
    }

    // Inject headers
    if let Some(headers) = auth_data.get("headers") {
        let headers_map: std::collections::HashMap<String, String> = headers.as_object()
            .cloned().unwrap_or_default()
            .iter().map(|(k, v)| (k.clone(), v.as_str().unwrap_or("").to_string())).collect();
        context.set_extra_http_headers(headers_map.into_iter()).await?;
    }

    // Read back cookies to confirm
    let js = r#"() => document.cookie.split(';').map(c => c.trim()).filter(Boolean)"#;
    let result: serde_json::Value = page.eval(js).await?;
    println!("{{\"cookies_count\": {}, \"injected\": true}}", result.as_array().map(|a| a.len()).unwrap_or(0));
    Ok(())
}

pub async fn action_auth_clear(page: &Page, _args: &CliArgs) -> Result<()> {
    let js = r#"() => {
        document.cookie.split(';').forEach(c => {
            document.cookie = c.replace(/^ +/, '').replace(/=.*/, '=;expires=' + new Date().toUTCString() + ';path=/');
        });
    }"#;
    page.eval::<()>(js).await?;
    println!("{{\"cleared\": true}}");
    Ok(())
}

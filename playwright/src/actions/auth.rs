use anyhow::Result;
use playwright::{BrowserContext, Page};
use playwright::types::Cookie;
use crate::actions::CliArgs;
use crate::utils::extract_origin;

pub async fn action_auth_inject(page: &Page, context: &BrowserContext, args: &CliArgs) -> Result<()> {
    let url = args.url.clone().ok_or_else(|| anyhow::anyhow!("No URL"))?;
    let value = args.value.as_deref().ok_or_else(|| anyhow::anyhow!("No value"))?;
    let mode = args.output.as_deref().unwrap_or("");

    let data: serde_json::Value = serde_json::from_str(value)?;

    match mode {
        "cookies" => {
            let cookies: Vec<serde_json::Value> = serde_json::from_value(data)?;
            let origin = extract_origin(&url)?;
            for c in cookies {
                let cookie = Cookie::new()
                    .name(c["name"].as_str().unwrap_or(""))
                    .value(c["value"].as_str().unwrap_or(""))
                    .domain(c.get("domain").and_then(|v| v.as_str()).unwrap_or(&origin))
                    .path(c.get("path").and_then(|v| v.as_str()).unwrap_or("/"));
                context.add_cookie(&[cookie]).await?;
            }
            println!("[auth] Injected {} cookie(s)", cookies.len());
        }
        "localStorage" => {
            let kv: std::collections::HashMap<String, String> = serde_json::from_value(data)?;
            let origin = extract_origin(&url)?;
            let sets: Vec<String> = kv.iter().map(|(k, v)| {
                format!("localStorage.setItem({}, {});", serde_json::to_string(k)?, serde_json::to_string(v)?)
            }).collect::<Result<Vec<_>>>()?;
            let script = format!("(function() {{ if (location.origin === {}) {{ {} }} }})();",
                serde_json::to_string(&origin)?, sets.join(""));
            context.add_init_script(&script).await?;
            println!("[auth] Seeded {} localStorage key(s)", kv.len());
        }
        "headers" => {
            let hdrs: std::collections::HashMap<String, String> = serde_json::from_value(data)?;
            for (k, v) in &hdrs {
                context.set_extra_http_header(k, v).await?;
            }
            println!("[auth] Set {} extra HTTP header(s)", hdrs.len());
        }
        _ => {
            // Combined mode
            if let Some(cookies) = data.get("cookies") {
                if let Ok(arr) = serde_json::from_value::<Vec<serde_json::Value>>(cookies.clone()) {
                    let origin = extract_origin(&url)?;
                    for c in &arr {
                        let cookie = Cookie::new()
                            .name(c["name"].as_str().unwrap_or(""))
                            .value(c["value"].as_str().unwrap_or(""))
                            .domain(c.get("domain").and_then(|v| v.as_str()).unwrap_or(&origin));
                        context.add_cookie(&[cookie]).await?;
                    }
                }
            }
            if let Some(ls) = data.get("localStorage") {
                if let Ok(kv) = serde_json::from_value::<std::collections::HashMap<String, String>>(ls.clone()) {
                    let origin = extract_origin(&url)?;
                    let sets: Vec<String> = kv.iter().map(|(k, v)| {
                        format!("localStorage.setItem({}, {});", serde_json::to_string(k)?, serde_json::to_string(v)?)
                    }).collect::<Result<Vec<_>>>()?;
                    let script = format!("(function() {{ if (location.origin === {}) {{ {} }} }})();",
                        serde_json::to_string(&origin)?, sets.join(""));
                    context.add_init_script(&script).await?;
                }
            }
        }
    }

    Ok(())
}

pub async fn action_auth_clear(page: &Page, args: &CliArgs) -> Result<()> {
    let context = page.context();
    context.clear_cookies().await?;
    page.evaluate("localStorage.clear()").await?;
    println!("[auth] Cleared all auth state");
    Ok(())
}

use anyhow::Result;
use playwright::api::page::Page;
use crate::actions::CliArgs;

// Dialog API stubbed in 0.0.20 — use JS eval interceptors

pub async fn action_dialog_accept(page: &Page, _args: &CliArgs) -> Result<()> {
    // Pre-register alert/confirm handler
    let js = r#"(sel) => {
        window.addEventListener('alert', () => {}, true);
        const origAlert = window.alert;
        window.alert = () => {};
        return true;
    }"#;
    let result: bool = page.eval::<bool>(js).await.unwrap_or(false);
    println!("{{\"registered\": {}}}", result);
    Ok(())
}

pub async fn action_dialog_dismiss(page: &Page, _args: &CliArgs) -> Result<()> {
    // Pre-register dialog dismiss
    let js = r#"(sel) => {
        window.addEventListener('beforeunload', (e) => { e.returnValue = ''; }, true);
        const origConfirm = window.confirm;
        window.confirm = () => false;
        return true;
    }"#;
    let result: bool = page.eval::<bool>(js).await.unwrap_or(false);
    println!("{{\"registered\": {}}}", result);
    Ok(())
}

pub async fn action_dialog_prompt(page: &Page, args: &CliArgs) -> Result<()> {
    let val = args.value.as_deref().unwrap_or("");
    let val_json = serde_json::to_string(val)?;
    // Pre-register prompt handler
    let js = format!(
        r#"(sel) => {{
            const origPrompt = window.prompt;
            window.prompt = () => {};
            return true;
        }}"#,
        val_json
    );
    let result: bool = page.eval::<bool>(&js).await.unwrap_or(false);
    println!("{{\"registered\": {}}}", result);
    Ok(())
}

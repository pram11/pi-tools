use anyhow::Result;
use playwright::Page;
use crate::actions::CliArgs;

pub async fn action_dialog_accept(page: &Page, args: &CliArgs) -> Result<()> {
    page.on_dialog(|dialog| async move { dialog.accept().await.ok() }).await;
    if let Some(sel) = &args.selector {
        page.click(sel).await.ok();
    }
    println!("[dialog] dialog-accept handled");
    Ok(())
}

pub async fn action_dialog_dismiss(page: &Page, args: &CliArgs) -> Result<()> {
    page.on_dialog(|dialog| async move { dialog.dismiss().await.ok() }).await;
    if let Some(sel) = &args.selector {
        page.click(sel).await.ok();
    }
    println!("[dialog] dialog-dismiss handled");
    Ok(())
}

pub async fn action_dialog_prompt(page: &Page, args: &CliArgs) -> Result<()> {
    let prompt_text = args.value.as_deref().unwrap_or("");
    page.on_dialog(move |dialog| async move {
        if dialog.r#type().await == playwright::types::DialogType::Prompt {
            dialog.accept_with_text(prompt_text).await.ok();
        } else {
            dialog.accept().await.ok();
        }
    }).await;
    if let Some(sel) = &args.selector {
        page.click(sel).await.ok();
    }
    println!("[dialog] dialog-prompt handled");
    Ok(())
}

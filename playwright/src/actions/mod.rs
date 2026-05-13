pub mod navigate;
pub mod interaction;
pub mod extract;
pub mod screenshot;
pub mod form;
pub mod assertions;
pub mod network;
pub mod shadow;
pub mod iframe;
pub mod dialog;
pub mod upload;
pub mod auth;
pub mod tabs;

use anyhow::Result;
use clap::Parser;
use playwright::api::browser::Browser;
use playwright::api::browser_context::BrowserContext;
use playwright::api::page::Page;

// ── Action Dispatch ─────────────────────────────────────────────

pub async fn dispatch(
    action: &str,
    args: &CliArgs,
    _browser: &Browser,
    context: &BrowserContext,
    page: Page,
) -> Result<()> {
    match action {
        // Phase 1 — Core
        "navigate" => navigate::action_navigate(&page, args).await,
        "click" => interaction::action_click(&page, args).await,
        "type" => interaction::action_type(&page, args).await,
        "extract" => extract::action_extract(&page, args).await,
        "screenshot" => screenshot::action_screenshot(&page, args).await,
        "wait" => interaction::action_wait(&page, args).await,
        "eval" => interaction::action_eval(&page, args).await,
        "scroll" => interaction::action_scroll(&page, args).await,

        // Phase 3 — Form
        "form-detect" => form::action_form_detect(&page, args).await,
        "smart-fill" => form::action_smart_fill(&page, args).await,
        "submit" => form::action_submit(&page, args).await,
        "wizard" => form::action_wizard(&page, args).await,

        // Phase 4 — Data Extraction
        "scrape" => extract::action_scrape(&page, args).await,
        "extract-all" => extract::action_extract_all(&page, args).await,
        "network" => network::action_network(&page, args).await,
        "pdf" => network::action_pdf(&page, args).await,

        // Phase 5 — Assertions
        "expect-text" => assertions::action_assert_text(&page, args).await,
        "expect-visible" => assertions::action_assert_visible(&page, args).await,
        "expect-url" => assertions::action_assert_url(&page, args).await,
        "screenshot-diff" => screenshot::action_screenshot_diff(&page, args).await,
        "report" => assertions::action_report(&page, args).await,

        // Phase 6 — Shadow DOM
        "shadow-detect" => shadow::action_shadow_detect(&page, args).await,
        "shadow-query" => shadow::action_shadow_query(&page, args).await,
        "shadow-click" => shadow::action_shadow_click(&page, args).await,
        "shadow-fill" => shadow::action_shadow_fill(&page, args).await,
        "shadow-extract" => shadow::action_shadow_extract(&page, args).await,
        "shadow-pierce" => shadow::action_shadow_pierce(&page, args).await,

        // Phase 6 — iframe
        "iframe-list" => iframe::action_iframe_list(&page, args).await,
        "iframe-query" => iframe::action_iframe_query(&page, args).await,
        "iframe-click" => iframe::action_iframe_click(&page, args).await,
        "iframe-fill" => iframe::action_iframe_fill(&page, args).await,
        "iframe-extract" => iframe::action_iframe_extract(&page, args).await,

        // Phase 6 — Dialog
        "dialog-accept" => dialog::action_dialog_accept(&page, args).await,
        "dialog-dismiss" => dialog::action_dialog_dismiss(&page, args).await,
        "dialog-prompt" => dialog::action_dialog_prompt(&page, args).await,

        // Phase 6 — Upload
        "upload" => upload::action_upload(&page, args).await,
        "upload-detect" => upload::action_upload_detect(&page, args).await,

        // Phase 6 — Auth
        "auth-inject" => auth::action_auth_inject(&page, context, args).await,
        "auth-clear" => auth::action_auth_clear(&page, args).await,

        // Phase 6 — Tabs
        "tabs-open" => tabs::action_tabs_open(context, args).await,
        "tabs-list" => tabs::action_tabs_list(context, args).await,
        "tabs-switch" => tabs::action_tabs_switch(context, args).await,
        "tabs-close" => tabs::action_tabs_close(context, args).await,
        "tabs-close-all" => tabs::action_tabs_close_all(context, args).await,
        "tabs-broadcast" => tabs::action_tabs_broadcast(context, args).await,
        "tabs-gather" => tabs::action_tabs_gather(context, args).await,

        _ => anyhow::bail!("Unknown action: {action}"),
    }
}

#[derive(Parser, Debug)]
pub struct CliArgs {
    /// Target URL
    #[arg(global = true)]
    pub url: Option<String>,

    /// CSS selector
    #[arg(global = true)]
    pub selector: Option<String>,

    /// Value (type/eval/wait/JSON input)
    #[arg(global = true)]
    pub value: Option<String>,

    /// Output file path
    #[arg(global = true)]
    pub output: Option<String>,

    /// Baseline screenshot for diff comparison
    #[arg(global = true)]
    pub baseline: Option<String>,

    /// Navigation timeout in ms (default 30000)
    #[arg(global = true, default_value = "30000")]
    pub timeout: u64,

    /// Max retry attempts on crash/timeout (default 1)
    #[arg(global = true, default_value = "1")]
    pub retries: usize,

    /// 0-based index for extract-all (default: all)
    #[arg(global = true)]
    pub nth: Option<usize>,
}

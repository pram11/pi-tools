use anyhow::Result;
use clap::Parser;
use dialoguer::Input;
use lettre::{
    message::{header::ContentType, Mailbox, Message, MultiPart, SinglePart},
    transport::smtp::authentication::Credentials,
    transport::smtp::SmtpTransport,
    Transport,
};
use serde::{Deserialize, Serialize};
use std::fs;
use std::path::Path;

#[derive(Parser, Debug)]
#[command(name = "send_mail")]
#[command(about = "Send email via SMTP", long_about = None)]
struct Cli {
    #[arg(short, long, env = "MAIL_TO")]
    to: String,

    #[arg(short, long, env = "MAIL_FROM")]
    from: String,

    #[arg(short, long, env = "MAIL_SUBJECT")]
    subject: String,

    #[arg(long, env = "MAIL_BODY")]
    body: Option<String>,

    #[arg(long)]
    html: Option<String>,

    #[arg(long, env = "MAIL_HOST")]
    host: String,

    #[arg(short, long, default_value = "587")]
    port: u16,

    #[arg(long, env = "MAIL_USER")]
    user: Option<String>,

    #[arg(long, env = "MAIL_PASS")]
    pass: Option<String>,

    #[arg(long, default_value = "starttls")]
    tls: String,

    #[arg(short = 'e', long, help = "Path to .env file (overrides auto-detection)")]
    env_file: Option<String>,
}

#[derive(Debug, Serialize, Deserialize)]
pub struct MailConfig {
    pub to: String,
    pub from: String,
    pub subject: String,
    pub body: Option<String>,
    pub html: Option<String>,
    pub host: String,
    pub port: u16,
    pub user: Option<String>,
    pub pass: Option<String>,
    pub tls: String,
}

impl From<Cli> for MailConfig {
    fn from(cli: Cli) -> Self {
        Self {
            to: cli.to,
            from: cli.from,
            subject: cli.subject,
            body: cli.body,
            html: cli.html,
            host: cli.host,
            port: cli.port,
            user: cli.user,
            pass: cli.pass,
            tls: cli.tls,
        }
    }
}

impl MailConfig {
    pub fn from_env() -> Result<Self> {
        // Load .env BEFORE clap parses (clap reads env vars at parse time)
        let env_file = resolve_env_path()?;
        ensure_dotenv(&env_file)?;
        dotenvy::from_path(&env_file).ok();
        let cli = Cli::parse();
        Ok(cli.into())
    }
}

fn resolve_env_path() -> Result<std::path::PathBuf> {
    // Check for --env-file in args manually (before clap parses)
    let args: Vec<String> = std::env::args().collect();
    for i in 0..args.len() {
        if (args[i] == "--env-file" || args[i] == "-e") && i + 1 < args.len() {
            return Ok(std::path::PathBuf::from(args[i + 1].clone()));
        }
    }
    env_file_path()
}

fn env_file_path() -> Result<std::path::PathBuf> {
    let cwd = std::env::current_dir()?;

    // Check exe directory first
    if let Some(exe_dir) = std::env::current_exe()?.parent().map(|p| p.to_path_buf()) {
        let env_path = exe_dir.join(".env");
        if env_path.exists() {
            return Ok(env_path);
        }
    }

    // Check cwd
    let cwd_env = cwd.join(".env");
    if cwd_env.exists() {
        return Ok(cwd_env);
    }

    // Fallback: cwd/.env
    Ok(cwd.join(".env"))
}

fn ensure_dotenv(env_file: &Path) -> Result<()> {
    if env_file.exists() {
        return Ok(());
    }
    println!("\n.env not found. Setting up SMTP configuration...");
    println!("(Values stored in {} for future use)\n", env_file.display());
    let host: String = Input::<String>::new().with_prompt("SMTP Host").default("smtp.gmail.com".to_string()).interact_text()?;
    let port_str: String = Input::<String>::new().with_prompt("SMTP Port").default("587".to_string()).interact_text()?;
    let port: u16 = port_str.parse().unwrap_or(587);
    let tls: String = Input::<String>::new().with_prompt("TLS (starttls/none)").default("starttls".to_string()).interact_text()?;
    let user: String = Input::<String>::new().with_prompt("Username").interact_text()?;
    let pass: String = dialoguer::Password::new().with_prompt("Password/App Password").interact()?;
    let from: String = Input::<String>::new().with_prompt("From Email").interact_text()?;
    let content = format!(
        "MAIL_HOST={}\nMAIL_PORT={}\nMAIL_TLS={}\nMAIL_USER={}\nMAIL_PASS=\"{}\"\nMAIL_FROM={}\n",
        host, port, tls, user, pass, from
    );
    fs::write(env_file, content)?;
    println!("\n.env written. Re-run to send email.\n");
    std::process::exit(0);
}

pub fn build_email(config: &MailConfig) -> Result<Message> {
    let builder = Message::builder()
        .from(
            config
                .from
                .parse::<Mailbox>()
                .expect("Invalid from address"),
        )
        .to(
            config
                .to
                .parse::<Mailbox>()
                .expect("Invalid to address"),
        )
        .subject(&config.subject);

    let email = if let Some(html_body) = &config.html {
        let plain = config.body.as_deref().unwrap_or("");
        let multipart = MultiPart::alternative()
            .singlepart(SinglePart::plain(plain.to_string()))
            .singlepart(SinglePart::html(html_body.to_string()));
        builder.multipart(multipart)?
    } else {
        let body = config.body.as_deref().unwrap_or("No body provided");
        builder.header(ContentType::TEXT_PLAIN).body(body.to_string())?
    };

    Ok(email)
}

pub fn send_email_sync(config: &MailConfig) -> Result<()> {
    let email = build_email(config)?;

    let builder = match config.tls.as_str() {
        "starttls" => SmtpTransport::starttls_relay(&config.host)?.credentials(Credentials::new(
            config.user.clone().unwrap_or_default(),
            config.pass.clone().unwrap_or_default(),
        )),
        _ => SmtpTransport::builder_dangerous(&config.host)
            .port(config.port)
            .credentials(Credentials::new(
                config.user.clone().unwrap_or_default(),
                config.pass.clone().unwrap_or_default(),
            )),
    };

    let mailer = builder.build();
    let result = mailer.send(&email);
    match result {
        Ok(response) => {
            println!("Email sent successfully: {:?}", response);
            Ok(())
        }
        Err(e) => Err(anyhow::anyhow!("Failed to send email: {:?}", e)),
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    env_logger::init();
    let config = MailConfig::from_env()?;
    send_email_sync(&config)?;
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_build_email_text() {
        let config = MailConfig {
            to: "to@example.com".to_string(),
            from: "from@example.com".to_string(),
            subject: "Test Subject".to_string(),
            body: Some("Hello World".to_string()),
            html: None,
            host: "smtp.example.com".to_string(),
            port: 587,
            user: None,
            pass: None,
            tls: "starttls".to_string(),
        };
        let email = build_email(&config).unwrap();
        let formatted = String::from_utf8(email.formatted()).unwrap();
        assert!(formatted.contains("to@example.com"));
        assert!(formatted.contains("from@example.com"));
        assert!(formatted.contains("Test Subject"));
        assert!(formatted.contains("Hello World"));
    }

    #[test]
    fn test_build_email_html() {
        let config = MailConfig {
            to: "to@example.com".to_string(),
            from: "from@example.com".to_string(),
            subject: "HTML Email".to_string(),
            body: None,
            html: Some("<h1>Hello</h1>".to_string()),
            host: "smtp.example.com".to_string(),
            port: 587,
            user: None,
            pass: None,
            tls: "starttls".to_string(),
        };
        let email = build_email(&config).unwrap();
        let formatted = String::from_utf8(email.formatted()).unwrap();
        assert!(formatted.contains("<h1>Hello</h1>"));
    }

    #[test]
    fn test_env_file_path_returns_cwd_fallback() {
        let path = env_file_path().unwrap();
        assert!(path.ends_with(".env"));
    }

    #[test]
    fn test_env_file_path_prefers_existing() {
        let dir = std::env::temp_dir().join("sendmail_env_test");
        fs::create_dir_all(&dir).ok();
        let env_path = dir.join(".env");
        fs::write(&env_path, "MAIL_HOST=test").ok();

        // Simulate: if cwd has .env, it should be found
        let original_dir = std::env::current_dir().unwrap();
        std::env::set_current_dir(&dir).ok();
        let found = env_file_path().unwrap();
        std::env::set_current_dir(&original_dir).ok();
        assert_eq!(found, env_path);
        fs::remove_dir_all(&dir).ok();
    }
}

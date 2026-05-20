use anyhow::Result;
use clap::Parser;
use lettre::{
    message::{header::ContentType, Mailbox, Message, MultiPart, SinglePart},
    transport::smtp::authentication::Credentials,
    transport::smtp::SmtpTransport,
    Transport,
};
use serde::{Deserialize, Serialize};

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

    #[arg(short, long, env = "MAIL_HOST")]
    host: String,

    #[arg(short, long, default_value = "587")]
    port: u16,

    #[arg(long, env = "MAIL_USER")]
    user: Option<String>,

    #[arg(long, env = "MAIL_PASS")]
    pass: Option<String>,

    #[arg(long, default_value = "starttls")]
    tls: String,
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
        let cli = Cli::parse();
        Ok(cli.into())
    }
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
            log::info!("Email sent successfully: {:?}", response);
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
}

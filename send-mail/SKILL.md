---
name: send-mail
description: Send emails via SMTP (Gmail compatible). Supports plain text + HTML multipart.
version: 0.1.0
---

# Send Mail Skill

Rust binary — uses `lettre` (latest) with rustls TLS. Single binary deploy.

## Usage

```bash
send_mail --to <recipient> --from <sender> --subject <subject> \
  --host <smtp_host> [--port 587] [--user <username>] [--pass <password>] \
  [--body "Plain text body"] [--html "<h1>HTML</h1>"] [--tls starttls]
```

### Arguments
| Arg | Short | Env | Description |
|---|---|---|---|
| `--to` | `-t` | `MAIL_TO` | Recipient address |
| `--from` | `-f` | `MAIL_FROM` | Sender address |
| `--subject` | `-s` | `MAIL_SUBJECT` | Email subject |
| `--body` | | `MAIL_BODY` | Plain text body (optional) |
| `--html` | | | HTML body (optional; creates multipart) |
| `--host` | `-h` | `MAIL_HOST` | SMTP server hostname |
| `--port` | `-p` | `MAIL_PORT` | SMTP port (default: 587) |
| `--user` | | `MAIL_USER` | Auth username |
| `--pass` | | `MAIL_PASS` | Auth password / app password |
| `--tls` | | `MAIL_TLS` | `starttls` (default) or `none` |

## Gmail Setup

1. Enable 2FA on Google Account.
2. Generate an App Password: Google Account → Security → App Passwords.
3. Use app password in `--pass` or `MAIL_PASS`.

```bash
MAIL_HOST=smtp.gmail.com MAIL_PORT=587 MAIL_TLS=starttls \
MAIL_USER=you@gmail.com MAIL_PASS="xxxx xxxx xxxx xxxx" \
./target/release/send-mail -t recipient@example.com -f you@gmail.com -s "Test" --body "Hello"
```

## Build

```bash
cd /root/.pi/agent/skills/send-mail
. "$HOME/.cargo/env"
cargo build --release
# Binary: target/release/send_mail
```

## Test

```bash
cargo test
```

## Output Schema

On success:
```
Email sent successfully: 250 2.0.0 OK <id>
```

On failure:
```
Error: Failed to send email: Connection refused
```

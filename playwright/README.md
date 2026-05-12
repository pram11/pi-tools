# Playwright Skill

Headless Chromium browser automation via Playwright Python API. 46 actions for E2E testing, scraping, form automation, and UI verification.

## Quick Start

```bash
pip install -r requirements.txt
python -m playwright install chromium

# Navigate + screenshot
python main.py --url https://example.com --action navigate
python main.py --action screenshot --output page.png
```

## Actions (46)

Full reference → [SKILL.md](./SKILL.md)

| Tier | Actions |
|---|---|
| **Core** (8) | navigate, click, type, extract, screenshot, wait, eval, scroll |
| **Form** (4) | form-detect, smart-fill, submit, wizard |
| **Extraction** (4) | scrape, extract-all, network, pdf |
| **Assertions** (5) | expect-text, expect-visible, expect-url, screenshot-diff, report |
| **Advanced** (21) | shadow-*, iframe-*, dialog-*, upload, auth-*, tabs-* |

## Session Mode

Persistent browser context with cookie/localStorage persistence:

```bash
python main.py session-start --url https://example.com
python main.py --action click --selector "#btn"
python main.py --action extract --selector "h1"
python main.py session-stop
```

## Architecture

- Single-process CLI (`main.py`) driving headless Chromium
- Session state in SQLite (`.sessions/state.db`) + Playwright storage_state JSON
- Auto-recovery on page crash / navigation timeout (`--retries N`)
- All actions return to stdout (JSON or plain text); errors to stderr with exit code 1

## Testing

```bash
.venv/bin/python -m pytest tests/
```

## Project Scope

Headless browser automation — navigation, interaction, extraction, screenshots, assertions, form flows, data scraping, shadow DOM, iframes, dialogs, file upload, auth, multi-tab orchestration.

## License

MIT (inherited from pi-tools)

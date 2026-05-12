# playwright-md

**URL → Markdown in one command.** Chains Playwright (headless Chromium) + html2md (HTML→MD converter).

```bash
python main.py --url https://example.com
```

## Install

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

## Usage

### Single URL
```bash
python main.py --url https://example.com
python main.py --url https://example.com --output page.md
```

### Wait for Dynamic Content
```bash
python main.py --url https://app.com --wait-for "#content" --timeout 15000
```

### Sub-Region Extraction
```bash
python main.py --url https://docs.example.com --selector "main article"
```

### Auth (Cookies + Headers)
```bash
python main.py --url https://app.com \
  --cookies '[{"name":"sid","value":"abc","domain":".app.com"}]' \
  --headers '{"User-Agent":"my-bot"}'
```

### Batch Mode
```bash
# urls.txt: one URL per line
python main.py --urls urls.txt --output-dir ./output/
```

### Switch Backend
```bash
python main.py --url https://example.com --backend html2text
```

## Pipeline

```
URL → Playwright → wait → extract HTML → sanitize → convert → post-process → Markdown
```

## Args

| Flag | Default | Description |
|---|---|---|
| `--url` | — | Target URL |
| `--urls` | — | File with URLs (batch) |
| `--output` | stdout | Write to file |
| `--output-dir` | — | Output dir (batch) |
| `--wait-for` | — | CSS selector to wait for |
| `--wait-for-url` | — | URL substring to wait for |
| `--timeout` | 30000 | Navigation timeout (ms) |
| `--retries` | 1 | Retry count |
| `--selector` | — | CSS selector (sub-region) |
| `--backend` | markdownify | Converter backend |
| `--cookies` | — | JSON cookie array |
| `--headers` | — | JSON header dict |
| `--session-dir` | `.sessions/` | Persistent state dir |

## Skills Used
- `../playwright/` — browser automation
- `../html2md/` — HTML→Markdown conversion

## License
MIT

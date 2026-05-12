# playwright-md Skill — Structure & Architecture

## Design Philosophy
Single-process CLI orchestrating two sibling skills. No forking external processes — direct Python API imports from `playwright` and `html2md` packages. One command, one output.

## Directory Structure

```text
playwright-md/                 # Skill root (portable)
├── SKILL.md                   # Skill spec — agent entry point
├── PLAN.md                    # Implementation roadmap
├── STRUCTURE.md               # This file
├── AGENTS.md                  # Coding standards & workflow
├── requirements.txt           # Dependencies
├── main.py                    # CLI entry point (argparse → orchestrator)
├── lib/                       # Shared modules
│   ├── orchestrator.py        # Core pipeline: navigate → extract → convert
│   ├── path_resolver.py       # Resolve sibling skill paths (playwright, html2md)
│   └── auth_helper.py         # Cookie/header injection utilities
├── scripts/                   # Helper scripts
│   └── batch_urls.py          # Multi-URL batch processor
├── tests/                     # Test suite
│   ├── test_orchestrator.py   # Pipeline unit tests
│   └── test_e2e.py            # E2E smoke test
└── .sessions/                 # Persistent browser state (auto-created)
```

## Architectural Decisions

### 1. Import Strategy — Direct API, Not Process Fork
- `playwright` skill → import Python API directly (`from playwright.sync_api import sync_playwright`)
- `html2md` skill → import conversion pipeline (`from html2md.lib.md_converter import ...`)
- No `subprocess` calls. No shell pipes. Single process = lower overhead + better error handling.

### 2. Path Resolution — Relative to Skill Root
```python
SKILL_ROOT = Path(__file__).resolve().parent
PLAYWRIGHT_PATH = SKILL_ROOT / "../playwright"
HTML2MD_PATH = SKILL_ROOT / "../html2md"
```
- Portable: move entire `playwright-md/` dir, paths auto-adjust.
- `sys.path.insert()` used to enable direct imports.

### 3. Pipeline Stages (Linear, Fail-Fast)
```
Stage 1: Browser Init     → playwright.sync_api().chromium.launch()
Stage 2: Navigate          → page.goto(url, timeout=MS)
Stage 3: Wait Conditions   → page.wait_for_selector() / wait_for_url()
Stage 4: Extract HTML      → page.evaluate("document.documentElement.outerHTML")
Stage 5: Sanitize          → BeautifulSoup strip <script>/<style>
Stage 5.5: Core Extract    → strip nav/header/footer/aside + class patterns (optional, --core-only)
Stage 6: Convert           → html2md backend (markdownify / html2text)
Stage 7: Post-Process      → dedup blanks, normalize whitespace
Stage 8: Output            → stdout or file
```
Any stage failure → stderr log + exit 1. Browser always `close()` in `finally`.

### 4. Auth Injection — Playwright API
- Cookies → `context.add_cookies()`
- Headers → `page.set_extra_http_headers()`
- Applied post-launch, pre-navigate.

### 5. Backend Selection — html2md Strategy Pattern
- Default: `markdownify` (GFM support, table handling)
- Fallback: `html2text` (aggressive simplification)
- Controlled via `--backend` flag, delegated to html2md skill's converter.

### 6. Session Persistence — Optional
- When `--session-dir` provided → reuse Playwright `storage_state` JSON
- Mirrors existing playwright skill session mode
- Enables auth state carry-across invocations

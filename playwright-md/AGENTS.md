# Pi playwright-md

This file defines coding standards, command protocols, and autonomous behavior for the playwright-md skill.

## Architecture
- Single-process CLI (`main.py`) orchestrating Playwright + html2md via direct Python API imports.
- Linear pipeline: navigate → wait → extract → sanitize → convert → output.
- Sibling skill path resolution relative to `main.py`.

## Plan
See [`PLAN.md`](./PLAN.md) for roadmap and milestones.
See [`STRUCTURE.md`](./STRUCTURE.md) for architecture decisions.

## Project Scope
- **Focus**: URL → Markdown in single command. JS-rendered pages supported.
- **Goal**: Eliminate 2-step manual piping. One invocation, one output.
- **Dependencies**: `playwright` skill (browser), `html2md` skill (converter).

## Core Commands
- **Setup**: `pip install -r requirements.txt && python -m playwright install chromium`
- **Basic**: `python main.py --url <URL> --action page-to-md`
- **To file**: `python main.py --url <URL> --action page-to-md --output result.md`
- **With auth**: `python main.py --url <URL> --cookies '[{"name":"x","value":"y"}]'`
- **Tests**: `pytest tests/`

## Behavior & Workflow
1. **URL Required**: `page-to-md` action requires `--url`. No URL → error, no guess.
2. **Wait Before Extract**: Always honor `--wait-for` / `--wait-for-url` before extracting HTML.
3. **Sanitize Pre-Convert**: Strip `<script>`, `<style>`, `<noscript>` tags before html2md pipeline. Default behavior.
4. **Error Handling**: Wrap every pipeline stage in try/except. Log to stderr, exit code 1. Agent can retry with `--retries`.
5. **Cleanup**: `browser.close()` in `finally` block. No orphan Chromium processes.
6. **Output**: Markdown to stdout by default. `--output` redirects to file.
7. **Completion**: Lint + test pass → commit & push.

## Git Protocol
- **Message Format**: `feat(playwright-md): <desc>`, `fix(playwright-md): <desc>`, `chore(playwright-md): <desc>`
- **Command**: `git add . && git commit -m "<message>" && git push`

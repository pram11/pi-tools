# Pi html2md

This file defines coding standards, command protocols, and autonomous behavior for the html2md skill.

## Architecture
- Single-process CLI (`main.py`) dispatching to strategy-pattern converters.
- Two backend plugins: `markdownify` (primary), `html2text` (fallback).
- Pipeline: `raw HTML → parser → converter → post-processor → Markdown`.

## Plan
See [`PLAN.md`](./PLAN.md) for roadmap and milestones.

## Project Scope
- **Focus**: Pure HTML → Markdown conversion. No network, no URL fetching.
- **Goal**: Deterministic, agent-runnable converter with pluggable backends.
- **Integration**: Playwright skill chains externally (`page.content()` → pipe to this skill).

## Core Commands
- **Setup**: `pip install -r requirements.txt`
- **From file**: `python main.py --file <path.html>`
- **From string**: `python main.py --html "<div>content</div>"`
- **Stdin**: `echo "<h1>hi</h1>" | python main.py`
- **To file**: `python main.py --file page.html --output result.md`
- **Switch backend**: `python main.py --file page.html --backend html2text`
- **Tests**: `pytest tests/`

## Behavior & Workflow
1. **Input Priority**: `--file` > `--html` > stdin. If none provided → error + usage.
2. **Backend Selection**: Default `markdownify`. Fallback to `html2text` on failure or explicit `--backend` flag.
3. **Sanitize First**: Always run HTML through BeautifulSoup parser before conversion. Strips script/style tags.
4. **Error Handling**: Wrap every conversion in try/except. Log to stderr, exit code 1 on failure. Agent can retry with alternate backend.
5. **Output**: Markdown to stdout by default. `--output` flag redirects to file.
6. **Completion**: Lint + test pass → commit & push.

## Git Protocol
- **Message Format**: `feat(html2md): <desc>`, `fix(html2md): <desc>`, `chore(html2md): <desc>`
- **Command**: `git add . && git commit -m "<message>" && git push`

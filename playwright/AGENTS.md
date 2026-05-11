# Pi Playwright

This file defines coding standards, command protocols, and autonomous behavior for the Playwright skill.

## Architecture
- Single-process CLI (`main.py`) driving headless Chromium.
- Session state persisted in SQLite (`.sessions/state.db`).
- Helper scripts in `scripts/`.

## Plan
See [`PLAN.md`](./PLAN.md) for roadmap and milestones.

## Project Scope
- **Focus**: Headless browser automation — navigation, interaction, extraction, screenshots.
- **Goal**: Agent-runnable UI automation with deterministic pass/fail signals.

## Core Commands
- **Setup**: `pip install -r requirements.txt && python -m playwright install chromium`
- **Run action**: `python main.py --url <URL> --action <action> [--selector <CSS>] [--value <text>]`
- **Screenshot helper**: `python scripts/quick_screenshot.py <URL> [output.png]`
- **Tests**: `pytest tests/` (when added)

## Behavior & Workflow
1. **URL First**: Always target a URL before interacting. No URL → error, no guess.
2. **Selectors Over Fragile Waits**: Use explicit CSS selectors, not `page.wait_for_timeout()`. Prefer `wait_for_selector` or action auto-wait.
3. **Stateful When Needed**: Multi-step flows → use session mode (`session-start` / `session-stop`) to avoid browser spin-up overhead per action.
4. **Error Handling**: Wrap every action in try/except. Log to stderr, exit code 1 on failure. Agent can retry or adapt.
5. **Cleanup**: Always `browser.close()` in finally block. No orphan Chromium processes.
6. **Completion**: Lint + test pass → commit & push.

## Git Protocol
- **Message Format**: `feat(playwright): <desc>`, `fix(playwright): <desc>`, `chore(playwright): <desc>`
- **Command**: `git add . && git commit -m "<message>" && git push`

# Pi Code Analyst

This file defines the coding standards, command protocols, and autonomous behavior guidelines for the Pi Code Analyst project.

## Architecture
See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for system design, directory structure, and data schemas.

## Plan
See [`PLAN.md`](./PLAN.md) for project roadmap, milestones, and implementation details.

## Project Scope
- **Focus**: High-precision source code analysis and feature mapping.
- **Goal**: Automatically extract routes, UI elements, and structural metadata to provide a "Function Map" of any given codebase.

## Core Commands
- **Setup**: `pip install -r requirements.txt`
- **Execution**: `python main.py --path <target_directory>`
- **Validation**: `pytest tests/` | `flake8 .`

## Behavior & Workflow
1. **Context Awareness**: Before proposing modifications, run the analysis skill to map the current project structure.
2. **Strategy-Based Analysis**: Implement language-specific logic within `plugins/` following the base interface to ensure modularity.
3. **Async Native**: Use `asyncio` and `aiofiles` for all I/O-bound operations to maintain performance.
4. **Completion & Synchronization**: Upon successful completion of a task or milestone:
   - Perform a final linting and test pass.
   - **Commit and Push** changes to the remote repository with a clear, descriptive message.

## Git Protocol
- **Message Format**: `feat: <description>`, `fix: <description>`, or `docs: <description>`.
- **Command**: `git add . && git commit -m "<message>" && git push`

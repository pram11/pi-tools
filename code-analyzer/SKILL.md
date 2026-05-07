---
name: code-analyst
description: Performs deep static analysis of a codebase to generate a feature chart containing routes, UI selectors, and structural metadata.
version: 0.1.0
---

# Code Analyst Skill

This skill allows the agent to autonomously map the functional surface area of any source code directory.

## Usage
The agent invokes the skill via the CLI:

```bash
python main.py --path <directory_path> --mode <auto|regex|ast>
```
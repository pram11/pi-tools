# Implementation Roadmap: Code Insight Phase

## Phase 1: Core Scaffolding (Current)
- [ ] Establish `code-analyst/` directory structure.
- [ ] Implement `main.py` with dynamic plugin discovery and loading.
- [ ] Define the `BaseAnalyzer` abstract class in `base.py`.

## Phase 2: Analyzer Development (Immediate)
- [ ] Build the `RegexAnalyzer` for baseline multi-language support.
- [ ] Develop the `PythonASTAnalyzer` for high-fidelity Python mapping.
- [ ] Create a `ProjectDetector` utility to automate plugin selection.

## Phase 3: Refinement & Integration
- [ ] Standardize the JSON output for downstream E2E scenario generators.
- [ ] Implement token-optimization logic to condense analysis results for LLM context windows.
- [ ] Integrate with the `pi-mono` local skill registry.

## Phase 4: Automation & CI
- [ ] Setup automated "Commit and Push" triggers for the agent upon task completion.
- [ ] Add unit tests for each analyzer plugin.

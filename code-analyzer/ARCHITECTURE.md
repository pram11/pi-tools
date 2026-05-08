# Architecture: Plug-and-Play Code Analysis

## Design Philosophy
The system utilizes a **Strategy Pattern** to decouple the orchestration logic from specific language parsing. This allows the analyst to swap analysis engines dynamically based on the detected environment.

## Structural Components
1. **Core Router (`main.py`)**: The entry point that detects the project type (e.g., searching for `package.json`, `pom.xml`, or `requirements.txt`) and delegates tasks to the appropriate plugin.
2. **Skill Registry**: A mapping system that matches file extensions and frameworks to specific analyzer implementations.
3. **Abstract Interface (`base.py`)**: A strict contract requiring an `analyze()` method, ensuring all plugins return a standardized JSON schema.
4. **Plugin Layer**:
   - `RegexAnalyzer`: A robust fallback for generic pattern matching.
   - `PythonASTAnalyzer`: Deep structural parsing using Python's `ast` module.
   - `JSXASTAnalyzer`: Deep structural parsing of `.tsx`/`.jsx` using tree-sitter.

## Directory Structure
- `code-analyzer/`
  - `main.py` (Entry Point)
  - `base.py` (Interface Definitions)
  - `plugins/` (Language-specific Strategies)
  - `lib/` (Shared Utilities & Schema Models)

## Data Schema (Feature Chart)
Every analyzer must output the following structure:
```json
{
  "file_path": "string",
  "feature_type": "Route | Component | Logic",
  "identifiers": ["string"],
  "complexity_score": "integer"
}
"""ProjectDetector – heuristic project type identification."""

from pathlib import Path

_SIGNATURES = {
    "python": {"requirements.txt", "setup.py", "setup.cfg", "pyproject.toml", "Pipfile"},
    "javascript": {"package.json", "yarn.lock", "package-lock.json"},
    "typescript": {"tsconfig.json"},
    "java": {"pom.xml", "build.gradle", "build.gradle.kts"},
    "rust": {"Cargo.toml", "Cargo.lock"},
    "go": {"go.mod", "go.sum"},
    "ruby": {"Gemfile", "Gemfile.lock"},
    "dotnet": {"csproj", "sln", "fsproj"},
}


class ProjectDetector:
    """Detect project languages/ecosystems from marker files."""

    @staticmethod
    def detect(target: Path) -> list[str]:
        """Return list of detected project types."""
        target = target.resolve()
        if not target.is_dir():
            return ["unknown"]

        marker_names = {p.name.lower() for p in target.iterdir() if p.is_file()}
        detected: list[str] = []

        for lang, markers in _SIGNATURES.items():
            if markers & marker_names:
                detected.append(lang)

        if not detected:
            # Fallback: infer from file extensions
            exts = {p.suffix.lower() for p in target.rglob("*") if p.is_file() and p.suffix}
            ext_map = {
                ".py": "python", ".js": "javascript", ".ts": "typescript",
                ".java": "java", ".rs": "rust", ".go": "go", ".rb": "ruby",
            }
            for ext, lang in ext_map.items():
                if ext in exts:
                    detected.append(lang)

        return detected if detected else ["unknown"]

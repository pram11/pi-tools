#!/usr/bin/env python3
"""Code Analyzer CLI – static analysis entry point."""

import typer
from rich.console import Console

app = typer.Typer(rich_markup_mode="rich")
console = Console()


@app.command()
def main(
    target_path: str = typer.Argument(..., help="Directory or file to analyze"),
    lang: str = typer.Option("all", "--lang", "-l", help="Comma-separated languages"),
    depth: int = typer.Option(4, "--depth", "-d", help="Max nesting depth threshold"),
    fmt: str = typer.Option("markdown", "--format", "-f", help="Output format: json or markdown"),
):
    """Run static analysis on TARGET_PATH."""
    import os, json
    from pathlib import Path

    target = Path(target_path)
    if not target.exists():
        console.print(f"[red]Error:[/red] Path not found: {target_path}")
        raise typer.Exit(1)

    # Stub analysis – replace with real tree-sitter logic
    files = list(target.rglob("*")) if target.is_dir() else [target]
    report = {
        "target": str(target.resolve()),
        "files_analyzed": len(files),
        "languages": lang.split(","),
        "max_depth_threshold": depth,
        "findings": [],
    }

    if fmt == "json":
        console.print(json.dumps(report, indent=2))
    else:
        console.print(f"# Analysis Report: [bold]{target}[/bold]")
        console.print(f"- **Files**: {len(files)}")
        console.print(f"- **Languages**: {lang}")
        console.print(f"- **Max Depth Threshold**: {depth}")
        console.print("- **Findings**: *(no issues detected yet)*")


if __name__ == "__main__":
    app()

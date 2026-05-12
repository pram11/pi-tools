"""Batch processing: read URL list, dispatch per-URL page-to-md."""

from pathlib import Path


def read_url_list(path: str) -> list[str]:
    """Read one URL per line from file. Skip blanks and # comments."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"URL file not found: {path}")
    lines = p.read_text(encoding="utf-8").splitlines()
    urls = []
    for line in lines:
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            urls.append(stripped)
    return urls


def run_batch(
    url_file: str,
    output_dir: str | None = None,
    wait_for: str | None = None,
    wait_for_url: str | None = None,
    timeout: int = 30000,
    retries: int = 1,
    selector: str | None = None,
    backend: str = "markdownify",
    cookies: str | None = None,
    headers: str | None = None,
    session_dir: str | None = None,
    core_only: bool = False,
    core_selector: str | None = None,
) -> int:
    """Process each URL from file. Output to --output-dir or stdout."""
    from .orchestrator import run_page_to_md

    urls = read_url_list(url_file)
    if not urls:
        print("Warning: no URLs found in file", file=__import__("sys").stderr)
        return 0

    out_dir = Path(output_dir) if output_dir else None
    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)

    failed = 0
    for i, url in enumerate(urls, 1):
        if out_dir:
            safe_name = _safe_filename(url)
            output = str(out_dir / f"{safe_name}.md")
        else:
            output = None

        print(f"[{i}/{len(urls)}] {url}", file=__import__("sys").stderr)
        rc = run_page_to_md(
            url=url,
            output=output,
            wait_for=wait_for,
            wait_for_url=wait_for_url,
            timeout=timeout,
            retries=retries,
            selector=selector,
            backend=backend,
            cookies=cookies,
            headers=headers,
            session_dir=session_dir,
            core_only=core_only,
            core_selector=core_selector,
        )
        if rc != 0:
            failed += 1

    if failed:
        print(f"Batch complete: {failed}/{len(urls)} failed", file=__import__("sys").stderr)
        return 1
    print(f"Batch complete: {len(urls)}/{len(urls)} OK", file=__import__("sys").stderr)
    return 0


def _safe_filename(url: str) -> str:
    """Convert URL to safe filename. https://example.com/path → example.com_path"""
    import re
    # Remove protocol
    name = re.sub(r"^https?://", "", url)
    # Replace slashes and unsafe chars
    name = re.sub(r"[/?#&=]", "_", name)
    # Truncate
    return name[:200] if name else "unnamed"

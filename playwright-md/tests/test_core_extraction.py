"""Tests for core-data-only extraction (Phase 9)."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pytest


class TestExtractCoreStripsNonContent:
    """Strategy 1 — Heuristic CSS removal."""

    def test_strips_nav_tag(self):
        from lib.orchestrator import extract_core
        html = "<html><body><nav>Links</nav><article>Main content</article></body></html>"
        result = extract_core(html)
        assert "Main content" in result
        assert "<nav>" not in result

    def test_strips_header_tag(self):
        from lib.orchestrator import extract_core
        html = "<html><body><header>Logo</header><main>Content</main></body></html>"
        result = extract_core(html)
        assert "Content" in result
        assert "<header>" not in result

    def test_strips_footer_tag(self):
        from lib.orchestrator import extract_core
        html = "<html><body><main>Content</main><footer>Copyright</footer></body></html>"
        result = extract_core(html)
        assert "Content" in result
        assert "<footer>" not in result

    def test_strips_aside_tag(self):
        from lib.orchestrator import extract_core
        html = "<html><body><main>Content</main><aside>Sidebar</aside></body></html>"
        result = extract_core(html)
        assert "Content" in result
        assert "<aside>" not in result

    def test_strips_common_class_patterns(self):
        from lib.orchestrator import extract_core
        html = "<html><body><div class='nav-menu'>Menu</div><div class='ad-banner'>Ad</div><div class='main-content'>Content</div></body></html>"
        result = extract_core(html)
        assert "Content" in result
        assert "Menu" not in result
        assert "Ad" not in result


class TestExtractCoreMainTagPreference:
    """Strategy 2 — Prefer semantic main-content elements."""

    def test_prefers_main_tag(self):
        from lib.orchestrator import extract_core
        html = "<html><body><nav>Nav</nav><main id='core'><h1>Title</h1><p>Body</p></main><aside>Aside</aside><footer>Footer</footer></body></html>"
        result = extract_core(html)
        assert "<main" in result or "Title" in result
        assert "Body" in result

    def test_prefers_article_tag(self):
        from lib.orchestrator import extract_core
        html = "<html><body><nav>Nav</nav><article><h2>Article</h2><p>Text</p></article><footer>Foot</footer></body></html>"
        result = extract_core(html)
        assert "Article" in result
        assert "Text" in result

    def test_prefers_role_main(self):
        from lib.orchestrator import extract_core
        html = "<html><body><div role='main'><p>Core</p></div><nav>Nav</nav><aside>Side</aside></body></html>"
        result = extract_core(html)
        assert "Core" in result

    def test_fallback_text_density_no_main_tag(self):
        """When no main/article/role=main, pick div with highest text density."""
        from lib.orchestrator import extract_core
        html = "<html><body><div class='nav'><a>A</a><a>B</a><a>C</a><a>D</a></div><div class='content'><p>Long paragraph of actual content text that should be preferred over navigation links.</p></div></body></html>"
        result = extract_core(html)
        assert "Long paragraph" in result

    def test_core_only_returns_smaller_output(self):
        """Core extraction should produce smaller output than full HTML."""
        from lib.orchestrator import extract_core
        html = """
        <html><body>
        <nav>Nav link 1 | Nav link 2 | Nav link 3</nav>
        <header>Site Header with logo and stuff</header>
        <aside>Sidebar with ads and widgets</aside>
        <main><h1>Article Title</h1><p>Body text here.</p></main>
        <footer>Footer copyright 2024</footer>
        </body></html>
        """
        full = html.strip()
        core = extract_core(html).strip()
        assert len(core) < len(full), "Core output should be smaller than full HTML"


class TestExtractCoreSelectorOverride:
    """--core-selector explicit override."""

    def test_explicit_selector_override(self):
        from lib.orchestrator import extract_core
        html = "<html><body><div id='custom'><p>Picked</p></div><main><p>Default</p></main></body></html>"
        result = extract_core(html, core_selector="#custom")
        assert "Picked" in result
        assert "Default" not in result

    def test_explicit_selector_with_strip(self):
        """Even with explicit selector, still strip nav/header/footer inside."""
        from lib.orchestrator import extract_core
        html = "<html><body><div id='region'><nav>Nav</nav><p>Content</p><footer>Foot</footer></div></body></html>"
        result = extract_core(html, core_selector="#region")
        assert "Content" in result
        assert "Nav" not in result
        assert "Foot" not in result


class TestExtractCorePipelineIntegration:
    """Integration: extract_core between extract_sub_region → sanitize."""

    def test_core_after_sub_region(self):
        """selector first, then core on that region."""
        from lib.orchestrator import extract_sub_region, extract_core
        html = "<html><body><div id='page'><nav>Nav</nav><main><p>Body</p></main><aside>Side</aside></div></body></html>"
        region = extract_sub_region(html, "#page")
        core = extract_core(region)
        assert "Body" in core
        assert "Nav" not in core
        assert "Side" not in core


class TestCLIFlags:
    """CLI --core-only and --core-selector flags."""

    def test_core_only_flag_parsed(self, tmp_path):
        """--core-only flag should not cause parse error."""
        import subprocess
        main = Path(__file__).resolve().parent.parent / "main.py"
        result = subprocess.run(
            [sys.executable, str(main), "--url", "https://example.com", "--core-only", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0  # --help exits 0

    def test_core_selector_flag_parsed(self, tmp_path):
        """--core-selector flag should not cause parse error."""
        import subprocess
        main = Path(__file__).resolve().parent.parent / "main.py"
        result = subprocess.run(
            [sys.executable, str(main), "--url", "https://example.com", "--core-selector", "main", "--help"],
            capture_output=True, text=True
        )
        assert result.returncode == 0

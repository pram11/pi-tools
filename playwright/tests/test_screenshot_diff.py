"""Tests for Phase 5: Screenshot diffing — visual regression detection."""

import os
import tempfile
import pytest
from PIL import Image
from playwright.sync_api import sync_playwright
from main import diff_screenshots


@pytest.fixture
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        p = browser.new_page()
        yield p
        browser.close()


class TestDiffScreenshots:
    """diff_screenshots: compare two screenshots, return similarity + diff."""

    def test_identical_screenshots_are_100_percent(self, page):
        page.set_content("<h1 style='color:red'>hello</h1>")
        page.set_viewport_size({"width": 800, "height": 600})
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as a:
            path_a = a.name
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as b:
            path_b = b.name
        try:
            page.screenshot(path=path_a)
            page.screenshot(path=path_b)
            result = diff_screenshots(path_a, path_b)
            assert result["similarity"] == pytest.approx(1.0, abs=0.01)
            assert result["match"] is True
            assert os.path.exists(result["diff_path"])
        finally:
            for p in (path_a, path_b, result["diff_path"]):
                if os.path.exists(p):
                    os.unlink(p)

    def test_different_screenshots_below_threshold(self, page):
        page.set_viewport_size({"width": 800, "height": 600})
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as a:
            path_a = a.name
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as b:
            path_b = b.name
        try:
            page.set_content("<h1 style='background:red;width:100%;height:600px'>A</h1>")
            page.screenshot(path=path_a)
            page.set_content("<h1 style='background:blue;width:100%;height:600px'>B</h1>")
            page.screenshot(path=path_b)
            result = diff_screenshots(path_a, path_b, threshold=0.9)
            assert result["similarity"] < 0.9
            assert result["match"] is False
            assert os.path.exists(result["diff_path"])
        finally:
            for p in (path_a, path_b, result["diff_path"]):
                if os.path.exists(p):
                    os.unlink(p)

    def test_different_sizes_flagged_and_low_similarity(self, page):
        page.set_content("<div style='background:red;width:100%;height:100%'></div>")
        page.set_viewport_size({"width": 400, "height": 300})
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as a:
            path_a = a.name
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as b:
            path_b = b.name
        try:
            page.screenshot(path=path_a)
            page.set_content("<div style='background:blue;width:100%;height:100%'></div>")
            page.set_viewport_size({"width": 800, "height": 600})
            page.screenshot(path=path_b)
            result = diff_screenshots(path_a, path_b)
            # Different sizes → flagged, and different colors → low similarity
            assert result["size_mismatch"] is True
            assert result["similarity"] < 0.5
            assert result["match"] is False
        finally:
            for p in (path_a, path_b, result["diff_path"]):
                if os.path.exists(p):
                    os.unlink(p)

    def test_custom_diff_output_path(self, page):
        page.set_content("<h1>hi</h1>")
        page.set_viewport_size({"width": 800, "height": 600})
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as a:
            path_a = a.name
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as b:
            path_b = b.name
        diff_out = "/tmp/custom_diff.png"
        try:
            page.screenshot(path=path_a)
            page.screenshot(path=path_b)
            result = diff_screenshots(path_a, path_b, diff_path=diff_out)
            assert result["diff_path"] == diff_out
            assert os.path.exists(diff_out)
        finally:
            for p in (path_a, path_b, diff_out):
                if os.path.exists(p):
                    os.unlink(p)

    def test_missing_file_raises_valueerror(self, page):
        with pytest.raises(ValueError, match="not found"):
            diff_screenshots("/tmp/does_not_exist_1.png", "/tmp/does_not_exist_2.png")

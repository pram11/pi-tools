"""Tests for file upload automation."""

import json
import os
import tempfile
import pytest
from playwright.sync_api import sync_playwright

UPLOAD_HTML = """
<!DOCTYPE html>
<html><body>
<form id="upload-form">
  <input type="file" name="avatar" id="avatar" />
  <input type="file" name="docs" id="docs" multiple />
  <input type="submit" value="Upload" />
</form>
<div id="result"></div>
<script>
  document.getElementById('upload-form').addEventListener('change', function(e) {
    if (e.target.type === 'file') {
      var names = Array.from(e.target.files).map(f => f.name).join(', ');
      document.getElementById('result').textContent = names;
    }
  });
</script>
</body></html>
"""


@pytest.fixture
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        p = browser.new_page()
        p.set_content(UPLOAD_HTML)
        yield p
        browser.close()


def test_upload_single_file(page):
    """Upload single file via input[type=file]."""
    from main import upload_files

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"hello")
        f.flush()
        path = f.name

    try:
        result = upload_files(page, "#avatar", path)
        assert result["files_uploaded"] == 1
        assert "txt" in result["files"][0].lower()
    finally:
        os.unlink(path)


def test_upload_multiple_files(page):
    """Upload multiple files via input[type=file][multiple]."""
    from main import upload_files

    files = []
    for i in range(3):
        with tempfile.NamedTemporaryFile(suffix=f"_{i}.jpg", delete=False) as f:
            f.write(b"fake-img")
            f.flush()
            files.append(f.name)

    try:
        result = upload_files(page, "#docs", *files)
        assert result["files_uploaded"] == 3
        assert all("jpg" in fn.lower() for fn in result["files"])
    finally:
        for p in files:
            os.unlink(p)


def test_upload_nonexistent_file(page):
    """Raise on missing file path."""
    from main import upload_files
    with pytest.raises(FileNotFoundError):
        upload_files(page, "#avatar", "/no/such/file.txt")


def test_upload_no_selector(page):
    """Raise when selector not found."""
    from main import upload_files

    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as f:
        f.write(b"test")
        f.flush()
        path = f.name

    try:
        with pytest.raises(Exception):
            upload_files(page, "#nonexistent", path)
    finally:
        os.unlink(path)


def test_detect_upload_inputs(page):
    """Detect file input fields on page."""
    from main import detect_upload_inputs
    inputs = detect_upload_inputs(page)
    assert len(inputs) == 2
    names = [i["name"] for i in inputs]
    assert "avatar" in names
    assert "docs" in names


def test_detect_multiple_flag(page):
    """Multiple attribute reported correctly."""
    from main import detect_upload_inputs
    inputs = detect_upload_inputs(page)
    docs = next(i for i in inputs if i["name"] == "docs")
    assert docs["multiple"] is True
    avatar = next(i for i in inputs if i["name"] == "avatar")
    assert avatar["multiple"] is False


def test_action_upload_cli(page):
    """CLI action wrapper works."""
    from main import action_upload

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        f.write(b"a,b,c")
        f.flush()
        path = f.name

    class Args:
        action = "upload"
        selector = "#avatar"
        value = path

    try:
        # Captures print output
        import io, sys
        buf = io.StringIO()
        old = sys.stdout
        sys.stdout = buf
        action_upload(page, Args())
        sys.stdout = old
        output = buf.getvalue()
        assert "1" in output
    finally:
        os.unlink(path)

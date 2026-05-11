"""Tests for Shadow DOM piercing (Phase 6)."""

import json
import pytest
from playwright.sync_api import sync_playwright

SHADOW_HTML = """
<!DOCTYPE html>
<html><body>
<my-element id="host1">
  <template shadowrootmode="open">
    <div class="inner">
      <h2 class="title">Shadow Title 1</h2>
      <span class="value">42</span>
      <button class="action">Click Me</button>
    </div>
  </template>
</my-element>

<my-element id="host2">
  <template shadowrootmode="open">
    <div class="inner">
      <h2 class="title">Shadow Title 2</h2>
      <span class="value">99</span>
      <button class="action">Click Me</button>
    </div>
  </template>
</my-element>

<deep-nested id="deepHost">
  <template shadowrootmode="open">
    <div class="level1">
      <custom-child>
        <template shadowrootmode="open">
          <p class="deep-text">Deeply Nested Content</p>
        </template>
      </custom-child>
    </div>
  </template>
</deep-nested>

<slotted-component>
  <p class="light-text">Light DOM content</p>
  <template shadowrootmode="open">
    <slot></slot>
    <span class="shadow-extra">Shadow Extra</span>
  </template>
</slotted-component>

<p class="outside">Outside text</p>
</body></html>
"""


@pytest.fixture
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        p = browser.new_page()
        p.set_content(SHADOW_HTML)
        yield p
        browser.close()


def test_shadow_query_text(page):
    """Extract text from element inside shadow DOM."""
    from main import shadow_query
    result = shadow_query(page, "#host1", ".title")
    assert result == "Shadow Title 1"


def test_shadow_query_missing(page):
    """Return None when inner selector not found."""
    from main import shadow_query
    result = shadow_query(page, "#host1", ".nonexistent")
    assert result is None


def test_shadow_click(page):
    """Click element inside shadow DOM."""
    from main import shadow_click, shadow_query
    shadow_click(page, "#host1", ".action")
    # Verify button was clicked by checking it's still present (no JS handler)
    result = shadow_query(page, "#host1", ".action")
    assert result == "Click Me"


def test_shadow_extract_all(page):
    """Extract text from matching elements across multiple shadow hosts."""
    from main import shadow_extract_all
    results = shadow_extract_all(page, "my-element", ".value")
    assert results == ["42", "99"]


def test_shadow_pierce_deep(page):
    """Pierce multiple shadow DOM levels."""
    from main import shadow_pierce
    result = shadow_pierce(page, "#deepHost >> custom-child >> .deep-text")
    assert result == "Deeply Nested Content"


def test_shadow_pierce_not_found(page):
    """Raise ValueError when deep selector fails."""
    from main import shadow_pierce
    with pytest.raises(ValueError):
        shadow_pierce(page, "#host1 >> .nonexistent >> .also-missing")


def test_shadow_detect(page):
    """List all shadow hosts on page."""
    from main import shadow_detect
    hosts = shadow_detect(page)
    assert len(hosts) >= 4  # my-element x2, deep-nested, slotted-component


def test_shadow_type(page):
    """Type into input inside shadow DOM."""
    from main import shadow_fill
    html = """
    <!DOCTYPE html>
    <html><body>
    <input-host>
      <template shadowrootmode="open">
        <input type="text" id="innerInput" />
      </template>
    </input-host>
    </body></html>
    """
    page.set_content(html)
    shadow_fill(page, "input-host", "#innerInput", "hello shadow")
    value = page.evaluate("""
        () => document.querySelector('input-host')
            .shadowRoot.querySelector('#innerInput').value
    """)
    assert value == "hello shadow"


def test_action_shadow_query(page):
    """CLI action: shadow-query."""
    from main import action_shadow
    import argparse
    args = argparse.Namespace(
        action="shadow-query",
        selector="#host1",
        value=".title"
    )
    action_shadow(page, args)  # should print text to stdout


def test_action_shadow_extract(page):
    """CLI action: shadow-extract."""
    from main import action_shadow
    import argparse
    args = argparse.Namespace(
        action="shadow-extract",
        selector="my-element",
        value=".value"
    )
    action_shadow(page, args)


def test_action_shadow_pierce(page):
    """CLI action: shadow-pierce with deep selector."""
    from main import action_shadow
    import argparse
    args = argparse.Namespace(
        action="shadow-pierce",
        value="#deepHost >> custom-child >> .deep-text"
    )
    action_shadow(page, args)


def test_action_shadow_detect(page):
    """CLI action: shadow-detect lists hosts."""
    from main import action_shadow
    import argparse
    args = argparse.Namespace(
        action="shadow-detect",
        selector=None,
        value=None
    )
    action_shadow(page, args)

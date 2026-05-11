"""Parallel pages — multi-tab orchestration.

Phase 6: tab management, broadcast, gather, close.
"""

import pytest
from playwright.sync_api import sync_playwright
from main import (
    tabs_open,
    tabs_list,
    tabs_switch,
    tabs_close,
    tabs_broadcast,
    tabs_gather,
    tabs_close_all,
)


class FakeArgs:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


@pytest.fixture
def browser():
    with sync_playwright() as pw:
        b = pw.chromium.launch(headless=True)
        yield b
        b.close()


@pytest.fixture
def context(browser):
    ctx = browser.new_context()
    yield ctx
    ctx.close()


@pytest.fixture
def html_a():
    return "<h1 id='title'>Page A</h1><span id='data'>alpha</span>"


@pytest.fixture
def html_b():
    return "<h1 id='title'>Page B</h1><span id='data'>beta</span>"


@pytest.fixture
def html_c():
    return "<h1 id='title'>Page C</h1><span id='data'>gamma</span>"


class TestTabsOpen:
    def test_open_default_count(self, context):
        pages = tabs_open(context)
        assert len(pages) == 3

    def test_open_custom_count(self, context):
        pages = tabs_open(context, count=5)
        assert len(pages) == 5

    def test_pages_are_independent(self, context, html_a, html_b):
        pages = tabs_open(context, count=2)
        pages[0].goto(f"data:text/html,{html_a}")
        pages[1].goto(f"data:text/html,{html_b}")
        assert pages[0].inner_text("h1") == "Page A"
        assert pages[1].inner_text("h1") == "Page B"


class TestTabsList:
    def test_list_empty(self, context):
        result = tabs_list(context)
        # new context has no pages yet
        assert isinstance(result, list)

    def test_list_after_open(self, context, html_a):
        pages = tabs_open(context, count=2)
        for p in pages:
            p.goto(f"data:text/html,{html_a}")
        result = tabs_list(context)
        assert len(result) == 2
        # each entry has url, title, index
        for entry in result:
            assert "url" in entry
            assert "title" in entry
            assert "index" in entry


class TestTabsSwitch:
    def test_switch_by_index(self, context, html_a, html_b):
        pages = tabs_open(context, count=2)
        pages[0].goto(f"data:text/html,{html_a}")
        pages[1].goto(f"data:text/html,{html_b}")
        p = tabs_switch(context, 1)
        assert p.inner_text("h1") == "Page B"

    def test_switch_out_of_range(self, context):
        with pytest.raises((IndexError, ValueError)):
            tabs_switch(context, 99)


class TestTabsClose:
    def test_close_single(self, context):
        pages = tabs_open(context, count=3)
        tabs_close(context, 1)
        remaining = tabs_list(context)
        assert len(remaining) == 2

    def test_close_last(self, context):
        pages = tabs_open(context, count=1)
        tabs_close(context, 0)
        assert len(tabs_list(context)) == 0


class TestTabsCloseAll:
    def test_close_all(self, context):
        tabs_open(context, count=5)
        tabs_close_all(context)
        assert len(tabs_list(context)) == 0


class TestTabsBroadcast:
    def test_broadcast_navigate(self, context, html_a, html_b, html_c):
        pages = tabs_open(context, count=3)
        urls = [
            f"data:text/html,{html_a}",
            f"data:text/html,{html_b}",
            f"data:text/html,{html_c}",
        ]
        results = tabs_broadcast(context, "goto", [(u,) for u in urls])
        assert len(results) == 3
        # verify each tab loaded correct content
        titles = tabs_gather(context, lambda p: p.inner_text("h1"))
        assert titles == ["Page A", "Page B", "Page C"]

    def test_broadcast_extract(self, context, html_a, html_b):
        pages = tabs_open(context, count=2)
        pages[0].goto(f"data:text/html,{html_a}")
        pages[1].goto(f"data:text/html,{html_b}")
        results = tabs_broadcast(context, "inner_text", [("#data",)] * 2)
        assert results == ["alpha", "beta"]


class TestTabsGather:
    def test_gather_titles(self, context, html_a, html_b, html_c):
        pages = tabs_open(context, count=3)
        pages[0].goto(f"data:text/html,{html_a}")
        pages[1].goto(f"data:text/html,{html_b}")
        pages[2].goto(f"data:text/html,{html_c}")
        gathered = tabs_gather(context, lambda p: p.inner_text("h1"))
        assert gathered == ["Page A", "Page B", "Page C"]

    def test_gather_urls(self, context, html_a):
        pages = tabs_open(context, count=2)
        pages[0].goto(f"data:text/html,{html_a}")
        pages[1].goto("data:text/html,<h1>Other</h1>")
        gathered = tabs_gather(context, lambda p: p.url)
        assert len(gathered) == 2

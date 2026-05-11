"""Tests for Phase 5 test report output (passed/failed summary)."""

import json
import pytest
from playwright.sync_api import sync_playwright
from main import AssertionReport, run_assertions


@pytest.fixture
def page():
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        p = browser.new_page()
        yield p
        browser.close()


class TestAssertionReport:
    """AssertionReport accumulator."""

    def test_init(self):
        r = AssertionReport()
        assert r.passed == 0
        assert r.failed == 0
        assert r.results == []

    def test_record_pass(self):
        r = AssertionReport()
        r.record("expect-text", "#x", "hello", True)
        assert r.passed == 1
        assert r.failed == 0
        assert len(r.results) == 1
        assert r.results[0]["status"] == "PASS"

    def test_record_fail(self):
        r = AssertionReport()
        r.record("expect-visible", "#x", "visible", False, "not visible")
        assert r.failed == 1
        assert r.results[0]["status"] == "FAIL"
        assert r.results[0]["error"] == "not visible"

    def test_summary(self):
        r = AssertionReport()
        r.record("expect-text", "#a", "x", True)
        r.record("expect-text", "#b", "y", False, "mismatch")
        r.record("expect-url", "url", "data:", True)
        s = r.summary()
        assert s["total"] == 3
        assert s["passed"] == 2
        assert s["failed"] == 1

    def test_to_json(self):
        r = AssertionReport()
        r.record("expect-text", "#x", "hello", True)
        out = r.to_json()
        data = json.loads(out)
        assert data["passed"] == 1

    def test_to_text(self):
        r = AssertionReport()
        r.record("expect-text", "#x", "hello", True)
        r.record("expect-visible", "#y", "visible", False, "err")
        out = r.to_text()
        assert "1 passed" in out
        assert "1 failed" in out


class TestRunAssertions:
    """run_assertions: batch assertion runner returning report."""

    def test_all_pass(self, page):
        page.set_content("<div id='a'>hello</div><div id='b'>world</div>")
        specs = [
            {"type": "expect-text", "selector": "#a", "value": "hello"},
            {"type": "expect-visible", "selector": "#b"},
        ]
        report = run_assertions(page, specs)
        assert report.passed == 2
        assert report.failed == 0

    def test_mixed_results(self, page):
        page.set_content("<div id='a'>hello</div><div id='b' style='display:none'>x</div>")
        specs = [
            {"type": "expect-text", "selector": "#a", "value": "hello"},
            {"type": "expect-visible", "selector": "#b"},
            {"type": "expect-text", "selector": "#a", "value": "mismatch"},
        ]
        report = run_assertions(page, specs)
        assert report.passed == 1
        assert report.failed == 2

    def test_expect_url_pass(self, page):
        page.goto("data:text/html,<h1>test</h1>")
        specs = [{"type": "expect-url", "value": "data:text/html"}]
        report = run_assertions(page, specs)
        assert report.passed == 1

    def test_empty_specs(self, page):
        report = run_assertions(page, [])
        assert report.passed == 0
        assert report.failed == 0
        assert report.total() == 0

    def test_report_json_output(self, page):
        page.set_content("<div id='a'>ok</div>")
        specs = [
            {"type": "expect-text", "selector": "#a", "value": "ok"},
            {"type": "expect-text", "selector": "#missing", "value": "x"},
        ]
        report = run_assertions(page, specs)
        data = json.loads(report.to_json())
        assert data["total"] == 2
        assert data["passed"] == 1
        assert data["failed"] == 1

    def test_report_text_output(self, page):
        page.set_content("<div id='a'>ok</div>")
        specs = [
            {"type": "expect-text", "selector": "#a", "value": "ok"},
        ]
        report = run_assertions(page, specs)
        text = report.to_text()
        assert "1 passed" in text
        assert "0 failed" in text

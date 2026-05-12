"""Tests for base.py — BaseConverter abstract class."""

import pytest
from base import BaseConverter


class FakeConverter(BaseConverter):
    def convert(self, html: str) -> str:
        return f"[fake] {html}"


class TestBaseConverter:
    def test_is_abstract(self):
        with pytest.raises(TypeError):
            BaseConverter()

    def test_subclass_implementation(self):
        c = FakeConverter()
        assert c.convert("<h1>hi</h1>") == "[fake] <h1>hi</h1>"

    def test_name_property(self):
        c = FakeConverter()
        assert isinstance(c.name, str)

"""Tests for CFG rendering utilities."""

from __future__ import annotations

import pytest


class TestCfgImage:
    """Smoke tests for the cfg_image module."""

    def test_open_external_import(self) -> None:
        from retui.rendering.cfg_image import open_external

        assert callable(open_external)

    def test_mermaid_to_png_import(self) -> None:
        from retui.rendering.cfg_image import mermaid_to_png

        assert callable(mermaid_to_png)

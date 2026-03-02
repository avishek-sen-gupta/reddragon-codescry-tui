"""Tests for FunctionScreen COBOL language detection and whole-file reading."""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from retui.screens.function_screen import FunctionScreen


def _make_config():
    return SimpleNamespace(
        llm=SimpleNamespace(model="test/model", api_key_env="TEST_KEY"),
    )


def _make_repo(path: str = "/tmp/fake-repo"):
    return SimpleNamespace(name="test-repo", path=path)


def _make_screen(
    file_path: str = "src/main.py",
    symbol_info: dict = {},
    repo_path: str = "/tmp/fake-repo",
) -> FunctionScreen:
    config = _make_config()
    repo = _make_repo(repo_path)
    return FunctionScreen(
        config=config,
        repo=repo,
        bundle=None,
        file_path=file_path,
        symbol_info=symbol_info,
    )


class TestDetectLanguageCobol:
    def test_detects_cobol_from_symbol_language(self):
        screen = _make_screen(symbol_info={"language": "cobol", "name": "MAIN-PARA"})
        assert screen._detect_language() == "cobol"

    def test_detects_cobol_from_cbl_extension(self):
        screen = _make_screen(
            file_path="src/program.cbl",
            symbol_info={"name": "MAIN-PARA"},
        )
        assert screen._detect_language() == "cobol"

    def test_detects_cobol_from_cob_extension(self):
        screen = _make_screen(
            file_path="src/program.cob",
            symbol_info={"name": "MAIN-PARA"},
        )
        assert screen._detect_language() == "cobol"

    def test_existing_languages_unaffected(self):
        screen = _make_screen(symbol_info={"language": "java", "name": "foo"})
        assert screen._detect_language() == "java"

        screen = _make_screen(file_path="main.py", symbol_info={"name": "foo"})
        assert screen._detect_language() == "python"


class TestReadEntireFile:
    def test_reads_full_file_content(self, tmp_path):
        cobol_src = "IDENTIFICATION DIVISION.\nPROGRAM-ID. HELLO.\n"
        src_file = tmp_path / "hello.cbl"
        src_file.write_text(cobol_src)

        screen = _make_screen(
            file_path="hello.cbl",
            repo_path=str(tmp_path),
        )
        result = screen._read_entire_file()
        assert result == cobol_src

    def test_returns_empty_for_missing_file(self, tmp_path):
        screen = _make_screen(
            file_path="nonexistent.cbl",
            repo_path=str(tmp_path),
        )
        result = screen._read_entire_file()
        assert result == ""

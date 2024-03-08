from pathlib import Path
from unittest.mock import MagicMock

import pytest

from secureli.modules.language_analyzer.language_analyzer_services import (
    language_analyzer,
)


@pytest.fixture()
def mock_repo_files() -> MagicMock:
    mock_repo_files = MagicMock()
    mock_repo_files.list_repo_files.return_value = [
        Path("file1.txt"),
        Path("file2.txt"),
        Path("file3.txt"),
    ]
    mock_repo_files.load_file.return_value = "file_contents"
    return mock_repo_files


@pytest.fixture()
def mock_repo_files_value_error() -> MagicMock:
    mock_repo_files = MagicMock()
    mock_repo_files.list_repo_files.return_value = [
        Path("file1.txt"),
        Path("file2.txt"),
        Path("file3.txt"),
    ]
    mock_repo_files.load_file.side_effect = ValueError("test exception")
    return mock_repo_files


@pytest.fixture()
def mock_lexer_guesser_bad_lang() -> MagicMock:
    mock_lexer_guesser = MagicMock()
    mock_lexer_guesser.guess_lexer.return_value = "BadLang"
    return mock_lexer_guesser


@pytest.fixture()
def mock_lexer_guesser_python() -> MagicMock:
    mock_lexer_guesser = MagicMock()
    mock_lexer_guesser.guess_lexer.return_value = "Python"
    return mock_lexer_guesser


@pytest.fixture()
def language_analyzer_bad_lang(
    mock_repo_files: MagicMock,
    mock_lexer_guesser_bad_lang: MagicMock,
) -> language_analyzer.LanguageAnalyzerService:
    return language_analyzer.LanguageAnalyzerService(
        repo_files=mock_repo_files,
        lexer_guesser=mock_lexer_guesser_bad_lang,
    )


@pytest.fixture()
def language_analyzer_python(
    mock_repo_files: MagicMock,
    mock_lexer_guesser_python: MagicMock,
) -> language_analyzer.LanguageAnalyzerService:
    return language_analyzer.LanguageAnalyzerService(
        repo_files=mock_repo_files,
        lexer_guesser=mock_lexer_guesser_python,
    )


@pytest.fixture()
def language_analyzer_with_warnings(
    mock_repo_files_value_error: MagicMock,
    mock_lexer_guesser_python: MagicMock,
) -> language_analyzer.LanguageAnalyzerService:
    return language_analyzer.LanguageAnalyzerService(
        repo_files=mock_repo_files_value_error,
        lexer_guesser=mock_lexer_guesser_python,
    )


@pytest.fixture()
def folder_path() -> MagicMock:
    folder_path = MagicMock()
    return folder_path


def test_that_language_analyzer_removes_unsupported_languages(
    language_analyzer_bad_lang: language_analyzer.LanguageAnalyzerService,
    folder_path: MagicMock,
):
    percentages_per_language = language_analyzer_bad_lang.analyze(folder_path)

    assert "BadLang" not in percentages_per_language


def test_that_language_analyzer_includes_python(
    language_analyzer_python: language_analyzer.LanguageAnalyzerService,
    folder_path: MagicMock,
):
    analyze_result = language_analyzer_python.analyze(folder_path)

    assert "Python" in analyze_result.language_proportions
    assert analyze_result.language_proportions["Python"] == 1.0


def test_that_language_analyzer_displays_warnings(
    language_analyzer_with_warnings: language_analyzer.LanguageAnalyzerService,
    folder_path: MagicMock,
):
    analyze_result = language_analyzer_with_warnings.analyze(folder_path)

    assert len(analyze_result.skipped_files) == 3

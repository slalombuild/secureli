from unittest.mock import MagicMock

import pytest

from secureli.modules.language_analyzer import language_analyzer_services


# Register generic mocks you'd like available for every test.


@pytest.fixture()
def mock_echo() -> MagicMock:
    mock_echo = MagicMock()
    return mock_echo


@pytest.fixture()
def mock_logging_service() -> MagicMock:
    mock_logging_service = MagicMock()
    return mock_logging_service


@pytest.fixture()
def mock_language_analyzer() -> MagicMock:
    mock_language_analyzer = MagicMock()
    mock_language_analyzer.analyze.return_value = (
        language_analyzer_services.language_analyzer.AnalyzeResult(
            language_proportions={
                "RadLang": 0.75,
                "BadLang": 0.25,
            },
            skipped_files=[],
        )
    )

    return mock_language_analyzer


@pytest.fixture()
def mock_language_support() -> MagicMock:
    mock_language_support = MagicMock()
    mock_language_support.apply_support.return_value = (
        language_analyzer_services.language_support.LanguageMetadata(
            version="abc123", security_hook_id="security-hook"
        )
    )
    return mock_language_support


@pytest.fixture()
def mock_settings() -> MagicMock:
    mock_settings = MagicMock()
    return mock_settings

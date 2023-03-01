from unittest.mock import MagicMock

import pytest

from secureli.services.language_analyzer import AnalyzeResult
from secureli.services.language_support import LanguageMetadata


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
    mock_language_analyzer.analyze.return_value = AnalyzeResult(
        language_proportions={
            "RadLang": 0.75,
            "BadLang": 0.25,
        },
        skipped_files=[],
    )

    return mock_language_analyzer


@pytest.fixture()
def mock_language_support() -> MagicMock:
    mock_language_support = MagicMock()
    mock_language_support.apply_support.return_value = LanguageMetadata(
        version="abc123", security_hook_id="security-hook"
    )
    return mock_language_support

from unittest.mock import MagicMock

import pytest

from secureli.services.language_config import (
    LanguageConfigService,
    LanguageNotSupportedError,
    LoadLinterConfigsResult,
)


@pytest.fixture()
def mock_data_loader() -> MagicMock:
    mock_data_loader = MagicMock()
    mock_data_loader.return_value = "repos: [{ repo: 'mock-repo' }]"
    return mock_data_loader


@pytest.fixture()
def language_config_service(
    mock_data_loader: MagicMock,
) -> LanguageConfigService:
    return LanguageConfigService(
        command_timeout_seconds=300,
        data_loader=mock_data_loader,
        ignored_file_patterns=[],
    )


def test_that_language_config_service_treats_missing_templates_as_unsupported_language(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
):
    mock_data_loader.side_effect = ValueError
    with pytest.raises(LanguageNotSupportedError):
        language_config_service.get_language_config("BadLang", True)


def test_that_language_config_service_treats_missing_templates_as_unsupported_language_when_checking_versions(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
):
    mock_data_loader.side_effect = ValueError
    with pytest.raises(LanguageNotSupportedError):
        language_config_service.get_language_config("BadLang", True)


def test_that_version_identifiers_are_calculated_for_known_languages(
    language_config_service: LanguageConfigService,
):
    version = language_config_service.get_language_config("Python", True).version

    assert version != None


def test_that_language_config_service_templates_are_loaded_with_global_exclude_if_provided_multiple_patterns(
    language_config_service: LanguageConfigService,
):
    language_config_service.ignored_file_patterns = [
        "mock_pattern1",
        "mock_pattern2",
    ]
    result = language_config_service.get_language_config("Python", True)

    assert "exclude: ^(mock_pattern1|mock_pattern2)" in result.config_data


def test_that_language_config_service_templates_are_loaded_without_exclude(
    language_config_service: LanguageConfigService,
):
    language_config_service.ignored_file_patterns = []
    result = language_config_service.get_language_config("Python", True)

    assert "exclude:" not in result.config_data


def test_that_language_config_service_templates_are_loaded_without_linter_config_if_include_linter_is_false(
    language_config_service: LanguageConfigService,
):
    language_config_service.ignored_file_patterns = []
    result = language_config_service.get_language_config("Python", False)

    assert result.linter_config == LoadLinterConfigsResult(
        successful=True, linter_data=[]
    )


def test_that_language_config_service_does_nothing_when_pre_commit_settings_is_empty(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
):
    def mock_loader_side_effect(resource):
        # Language config file
        return """
            repos:
            -   repo: http://sample-repo.com/baddie-finder
                hooks:
                -    id: baddie-finder-hook
                     args:
                        - orig_arg
        """

    mock_data_loader.side_effect = mock_loader_side_effect

    result = language_config_service.get_language_config("Python", True)

    assert "orig_arg" in result.config_data


# ### _load_language_config_files ####
def test_that_language_config_service_langauge_config_gets_loaded(
    language_config_service: LanguageConfigService,
):
    result = language_config_service._load_linter_config_file("JavaScript")

    assert result.successful


def test_that_language_config_service_language_config_does_not_get_loaded(
    language_config_service: LanguageConfigService,
):
    result = language_config_service._load_linter_config_file("RadLang")

    assert not result.successful


def test_that_language_config_service_templates_are_loaded_with_global_exclude_if_provided(
    language_config_service: LanguageConfigService,
):
    language_config_service.ignored_file_patterns = ["mock_pattern"]
    result = language_config_service.get_language_config("Python", True)

    assert "exclude: mock_pattern" in result.config_data


def test_that_calculate_combined_configuration_adds_lint_config(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
):
    mock_scanner_config = "repos: [{ repo: 'scanner-pre-commit'}]"
    mock_linter_config = "repos: [{ repo: 'linter-pre-commit'}]"

    def data_loader_side_effect(*args, **kwargs):
        if "base" in args[0]:
            return mock_scanner_config
        elif "lint" in args[0]:
            return mock_linter_config
        else:
            return "repos: []"

    mock_data_loader.side_effect = data_loader_side_effect
    result = language_config_service._calculate_combined_configuration("RadLang", True)

    assert result == {
        "repos": [{"repo": "scanner-pre-commit"}, {"repo": "linter-pre-commit"}]
    }
    assert mock_data_loader.call_count == 2


def test_that_calculate_combined_configuration_ignores_lint_config(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
):
    mock_data_loader.return_value = "repos: [{ repo: 'scanner-pre-commit'}]"
    result = language_config_service._calculate_combined_configuration("RadLang", False)

    assert result == {"repos": [{"repo": "scanner-pre-commit"}]}
    assert mock_data_loader.call_count == 1


def test_that_calculate_combined_configuration_ignores_lint_config(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
):
    mock_data_loader.return_value = ""
    result = language_config_service._calculate_combined_configuration("RadLang", False)

    assert result == {"repos": []}

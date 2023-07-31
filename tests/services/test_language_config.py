import pytest
from unittest.mock import MagicMock


from secureli.services.language_config import (
    LanguageConfigService,
    LanguageNotSupportedError,
)

from secureli.repositories.settings import (
    PreCommitSettings,
    PreCommitRepo,
    PreCommitHook,
)


@pytest.fixture()
def mock_data_loader() -> MagicMock:
    mock_data_loader = MagicMock()
    mock_data_loader.return_value = "a: 1"
    return mock_data_loader


@pytest.fixture()
def settings_dict() -> dict:
    return PreCommitSettings(
        repos=[
            PreCommitRepo(
                url="http://example-repo.com/",
                hooks=[
                    PreCommitHook(
                        id="hook-id",
                        arguments=None,
                        additional_args=None,
                    )
                ],
            )
        ]
    ).dict()


@pytest.fixture()
def language_config_service(
    mock_data_loader: MagicMock,
    settings_dict: dict,
) -> LanguageConfigService:
    return LanguageConfigService(
        command_timeout_seconds=300,
        data_loader=mock_data_loader,
        ignored_file_patterns=[],
        pre_commit_settings=settings_dict,
    )


def test_that_language_config_service_treats_missing_templates_as_unsupported_language(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
):
    mock_data_loader.side_effect = ValueError
    with pytest.raises(LanguageNotSupportedError):
        language_config_service.get_language_config("BadLang")


def test_that_language_config_service_treats_missing_templates_as_unsupported_language_when_checking_versions(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
):
    mock_data_loader.side_effect = ValueError
    with pytest.raises(LanguageNotSupportedError):
        language_config_service.get_language_config("BadLang")


def test_that_version_identifiers_are_calculated_for_known_languages(
    language_config_service: LanguageConfigService,
):
    version = language_config_service.get_language_config("Python").version

    assert version != None


def test_that_language_config_service_templates_are_loaded_with_global_exclude_if_provided_multiple_patterns(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
):
    mock_data_loader.return_value = "yaml: data"
    language_config_service.ignored_file_patterns = [
        "mock_pattern1",
        "mock_pattern2",
    ]
    result = language_config_service.get_language_config("Python")

    assert "exclude: ^(mock_pattern1|mock_pattern2)" in result.config_data


def test_that_language_config_service_templates_are_loaded_without_exclude(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
    mock_open: MagicMock,
):
    mock_data_loader.return_value = "yaml: data"
    language_config_service.ignored_file_patterns = []
    result = language_config_service.get_language_config("Python")

    assert "exclude:" not in result.config_data


def test_that_language_config_service_overrides_arguments_in_a_security_hook(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
    settings_dict: dict,
    mock_open: MagicMock,
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

    language_config_service.pre_commit_settings.repos[
        0
    ].url = "http://sample-repo.com/baddie-finder"
    language_config_service.pre_commit_settings.repos[0].hooks[
        0
    ].id = "baddie-finder-hook"
    language_config_service.pre_commit_settings.repos[0].hooks[0].arguments = [
        "arg_a",
        "value_a",
    ]

    mock_data_loader.side_effect = mock_loader_side_effect

    result = language_config_service.get_language_config("Python")

    assert "arg_a" in result.config_data
    assert "value_a" in result.config_data
    # Assert the original argument was removed
    assert "orig_arg" not in result.config_data


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

    result = language_config_service.get_language_config("Python")

    assert "orig_arg" in result.config_data


def test_that_language_config_service_overrides_arguments_do_not_apply_to_a_different_hook_id(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
    settings_dict: dict,
    mock_open: MagicMock,
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

    language_config_service.pre_commit_settings.repos[
        0
    ].url = "http://sample-repo.com/baddie-finder"
    language_config_service.pre_commit_settings.repos[0].hooks[
        0
    ].id = "goodie-finder-hook"  # doesn't match
    language_config_service.pre_commit_settings.repos[0].hooks[0].arguments = [
        "arg_a",
        "value_a",
    ]

    mock_data_loader.side_effect = mock_loader_side_effect

    result = language_config_service.get_language_config("RadLang")

    assert "arg_a" not in result.config_data
    assert "value_a" not in result.config_data
    # assert the original arg was left in place
    assert "orig_arg" in result.config_data


def test_that_language_config_service_adds_additional_arguments_to_a_hook(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
    settings_dict: dict,
    mock_open: MagicMock,
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

    language_config_service.pre_commit_settings.repos[
        0
    ].url = "http://sample-repo.com/baddie-finder"
    language_config_service.pre_commit_settings.repos[0].hooks[
        0
    ].id = "baddie-finder-hook"
    language_config_service.pre_commit_settings.repos[0].hooks[0].additional_args = [
        "arg_a",
        "value_a",
    ]

    mock_data_loader.side_effect = mock_loader_side_effect

    result = language_config_service.get_language_config("RadLang")

    assert "arg_a" in result.config_data
    assert "value_a" in result.config_data
    # assert the original arg was left in place
    assert "orig_arg" in result.config_data


def test_that_language_config_service_adds_additional_arguments_to_a_hook_if_the_hook_did_not_have_any_originally(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
    settings_dict: dict,
    mock_open: MagicMock,
):
    def mock_loader_side_effect(resource):
        # Language config file
        return """
            repos:
            -   repo: http://sample-repo.com/baddie-finder
                hooks:
                -    id: baddie-finder-hook
        """

    language_config_service.pre_commit_settings.repos[
        0
    ].url = "http://sample-repo.com/baddie-finder"
    language_config_service.pre_commit_settings.repos[0].hooks[
        0
    ].id = "baddie-finder-hook"
    language_config_service.pre_commit_settings.repos[0].hooks[0].additional_args = [
        "arg_a",
        "value_a",
    ]

    mock_data_loader.side_effect = mock_loader_side_effect

    result = language_config_service.get_language_config("RadLang")

    assert "arg_a" in result.config_data
    assert "value_a" in result.config_data


def test_that_language_config_service_excludes_files_in_specific_hooks(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
):
    def mock_loader_side_effect(resource):
        # Language config file
        return """
        repos:
        -   repo: http://example-repo.com/
            rev: 1.0.25
            hooks:
            -    id: hook-id
            -    id: hook-id-2
        """

    language_config_service.pre_commit_settings.repos[0].hooks[
        0
    ].exclude_file_patterns = ["file_a.py"]
    mock_data_loader.side_effect = mock_loader_side_effect

    result_1 = language_config_service.get_language_config("RadLang")

    language_config_service.pre_commit_settings.repos[0].hooks[
        0
    ].exclude_file_patterns = []

    result_2 = language_config_service.get_language_config("RadLang")

    assert "file_a" in result_1.config_data
    assert "file_a" not in result_2.config_data


def test_that_language_config_service_suppresses_hooks_in_repo(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
):
    def mock_loader_side_effect(resource):
        # Language config file
        return """
        repos:
        -   repo: http://example-repo.com/
            rev: 1.0.25
            hooks:
            -    id: hook-id
            -    id: hook-id-2
        """

    language_config_service.pre_commit_settings.repos[0].suppressed_hook_ids = [
        "hook-id-2"
    ]
    mock_data_loader.side_effect = mock_loader_side_effect

    result = language_config_service.get_language_config("RadLang")

    assert "hook-id-2" not in result.config_data
    assert "hook-id" in result.config_data


def test_that_language_config_service_removes_repo_when_all_hooks_suppressed(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
):
    def mock_loader_side_effect(resource):
        # Language config file
        return """
        repos:
        -   repo: http://example-repo.com/
            rev: 1.0.25
            hooks:
            -    id: hook-id
            -    id: hook-id-2
        """

    language_config_service.pre_commit_settings.repos[0].suppressed_hook_ids = [
        "hook-id",
        "hook-id-2",
    ]
    mock_data_loader.side_effect = mock_loader_side_effect

    result = language_config_service.get_language_config("RadLang")

    assert "http://example-repo.com/" not in result.config_data


def test_that_language_config_service_removes_the_one_hook_multiple_times_without_a_problem(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
):
    def mock_loader_side_effect(resource):
        # Language config file
        return """
        repos:
        -   repo: http://example-repo.com/
            rev: 1.0.25
            hooks:
            -    id: hook-id
        """

    language_config_service.pre_commit_settings.repos[0].suppressed_hook_ids = [
        "hook-id",
        "hook-id",
    ]
    mock_data_loader.side_effect = mock_loader_side_effect

    result = language_config_service.get_language_config("RadLang")

    assert "hook-id" not in result.config_data


def test_that_language_config_service_removes_repo_when_repo_suppressed(
    language_config_service: LanguageConfigService,
    mock_data_loader: MagicMock,
):
    def mock_loader_side_effect(resource):
        # Language config file
        return """
        repos:
        -   repo: http://example-repo.com/
            rev: 1.0.25
            hooks:
            -    id: hook-id
            -    id: hook-id-2
        """

    language_config_service.pre_commit_settings.suppressed_repos = [
        "http://example-repo.com/"
    ]
    mock_data_loader.side_effect = mock_loader_side_effect

    result = language_config_service.get_language_config("RadLang")

    assert "http://example-repo.com/" not in result.config_data


#### _load_language_config_files ####
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
    mock_data_loader: MagicMock,
    mock_open: MagicMock,
):
    mock_data_loader.return_value = "yaml: data"
    language_config_service.ignored_file_patterns = ["mock_pattern"]
    result = language_config_service.get_language_config("Python")

    assert "exclude: mock_pattern" in result.config_data

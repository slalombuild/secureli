from subprocess import CompletedProcess
from unittest.mock import MagicMock
import hashlib

import pytest
import yaml
from pytest_mock import MockerFixture

from secureli.abstractions.pre_commit import (
    PreCommitAbstraction,
    LanguageNotSupportedError,
    InstallFailedError,
)
from secureli.repositories.settings import (
    PreCommitSettings,
    PreCommitRepo,
    PreCommitHook,
)


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
def mock_data_loader() -> MagicMock:
    mock_data_loader = MagicMock()
    mock_data_loader.return_value = "a: 1"
    return mock_data_loader


@pytest.fixture()
def mock_open_config(mocker: MockerFixture) -> MagicMock:
    mock_open = mocker.mock_open(
        read_data="""
    exclude: some-exclude-regex
    repos:
    - hooks:
      - id: some-test-hook
      repo: xyz://some-test-repo-url
      rev: 1.0.0
    - hooks:
      - id: some-other-test-hook
      repo: xyz://some-other-test-repo-url
      rev: 1.0.0
    """
    )
    mocker.patch("builtins.open", mock_open)


@pytest.fixture()
def mock_subprocess(mocker: MockerFixture) -> MagicMock:
    mock_subprocess = MagicMock()
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    mocker.patch("secureli.abstractions.pre_commit.subprocess", mock_subprocess)
    return mock_subprocess


@pytest.fixture()
def mock_hashlib(mocker: MockerFixture) -> MagicMock:
    mock_hashlib = MagicMock()
    mock_md5 = MagicMock()
    mock_hashlib.md5.return_value = mock_md5
    mock_md5.hexdigest.return_value = "mock-hash-code"
    mocker.patch("secureli.abstractions.pre_commit.hashlib", mock_hashlib)
    return mock_hashlib


@pytest.fixture()
def mock_hashlib_no_match(mocker: MockerFixture) -> MagicMock:
    mock_hashlib = MagicMock()
    mock_md5 = MagicMock()
    mock_hashlib.md5.return_value = mock_md5
    mock_md5.hexdigest.side_effect = ["first-hash-code", "second-hash-code"]
    mocker.patch("secureli.abstractions.pre_commit.hashlib", mock_hashlib)
    return mock_hashlib


@pytest.fixture()
def pre_commit(
    mock_hashlib: MagicMock,
    mock_data_loader: MagicMock,
    mock_open: MagicMock,
    mock_subprocess: MagicMock,
    settings_dict: dict,
) -> PreCommitAbstraction:
    return PreCommitAbstraction(
        command_timeout_seconds=300,
        data_loader=mock_data_loader,
        ignored_file_patterns=[],
        pre_commit_settings=settings_dict,
    )


def test_that_pre_commit_templates_are_loaded_for_supported_languages(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    pre_commit.install("Python")

    mock_subprocess.run.assert_called_with(["pre-commit", "install"])


def test_that_pre_commit_templates_are_loaded_with_global_exclude_if_provided(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    mock_subprocess: MagicMock,
):
    mock_data_loader.return_value = "yaml: data"
    pre_commit.ignored_file_patterns = ["mock_pattern"]

    result = pre_commit.install("Python")

    assert result.successful


def test_that_pre_commit_templates_are_loaded_without_exclude(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    mock_subprocess: MagicMock,
):
    mock_data_loader.return_value = "yaml: data"
    pre_commit.ignored_file_patterns = []

    result = pre_commit.install("Python")

    assert result.successful


def test_that_pre_commit_templates_are_loaded_with_global_exclude_if_provided_multiple_patterns(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    mock_open: MagicMock,
):
    mock_data_loader.return_value = "yaml: data"
    pre_commit.ignored_file_patterns = [
        "mock_pattern1",
        "mock_pattern2",
    ]
    result = pre_commit.install("Python")

    assert result.successful


def test_that_pre_commit_treats_missing_templates_as_unsupported_language(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    mock_subprocess: MagicMock,
):
    mock_data_loader.side_effect = ValueError
    with pytest.raises(LanguageNotSupportedError):
        pre_commit.get_configuration("BadLang")


def test_that_pre_commit_treats_failing_process_as_install_failed_error(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    with pytest.raises(InstallFailedError):
        pre_commit.install("Python")


def test_that_pre_commit_installs_config_while_creating_if_install_param_set(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    mock_subprocess: MagicMock,
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

    result = pre_commit.get_configuration("RadLang", True)

    assert result.install_result.successful


def test_that_pre_commit_overrides_arguments_in_a_security_hook(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    settings_dict: dict,
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

    pre_commit.pre_commit_settings.repos[0].url = "http://sample-repo.com/baddie-finder"
    pre_commit.pre_commit_settings.repos[0].hooks[0].id = "baddie-finder-hook"
    pre_commit.pre_commit_settings.repos[0].hooks[0].arguments = [
        "arg_a",
        "value_a",
    ]

    mock_data_loader.side_effect = mock_loader_side_effect

    result = pre_commit.get_configuration("RadLang")

    assert "arg_a" in result.config_data["repos"][0]["hooks"][0]["args"]
    assert "value_a" in result.config_data["repos"][0]["hooks"][0]["args"]
    assert "orig_arg" not in result.config_data["repos"][0]["hooks"][0]["args"]


def test_that_pre_commit_overrides_arguments_do_not_apply_to_a_different_hook_id(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    settings_dict: dict,
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

    pre_commit.pre_commit_settings.repos[0].url = "http://sample-repo.com/baddie-finder"
    pre_commit.pre_commit_settings.repos[0].hooks[
        0
    ].id = "goodie-finder-hook"  # doesn't match
    pre_commit.pre_commit_settings.repos[0].hooks[0].arguments = [
        "arg_a",
        "value_a",
    ]

    mock_data_loader.side_effect = mock_loader_side_effect

    result = pre_commit.get_configuration("RadLang")

    assert "arg_a" not in result.config_data["repos"][0]["hooks"][0]["args"]
    assert "value_a" not in result.config_data["repos"][0]["hooks"][0]["args"]
    assert "orig_arg" in result.config_data["repos"][0]["hooks"][0]["args"]


def test_that_pre_commit_adds_additional_arguments_to_a_hook(
    pre_commit: PreCommitAbstraction,
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

    pre_commit.pre_commit_settings.repos[0].url = "http://sample-repo.com/baddie-finder"
    pre_commit.pre_commit_settings.repos[0].hooks[0].id = "baddie-finder-hook"
    pre_commit.pre_commit_settings.repos[0].hooks[0].additional_args = [
        "arg_a",
        "value_a",
    ]

    mock_data_loader.side_effect = mock_loader_side_effect

    result = pre_commit.get_configuration("RadLang")

    assert "arg_a" in result.config_data["repos"][0]["hooks"][0]["args"]
    assert "value_a" in result.config_data["repos"][0]["hooks"][0]["args"]
    # assert the original arg was left in place
    assert "orig_arg" in result.config_data["repos"][0]["hooks"][0]["args"]


def test_that_pre_commit_adds_additional_arguments_to_a_hook_if_the_hook_did_not_have_any_originally(
    pre_commit: PreCommitAbstraction,
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

    pre_commit.pre_commit_settings.repos[0].url = "http://sample-repo.com/baddie-finder"
    pre_commit.pre_commit_settings.repos[0].hooks[0].id = "baddie-finder-hook"
    pre_commit.pre_commit_settings.repos[0].hooks[0].additional_args = [
        "arg_a",
        "value_a",
    ]

    mock_data_loader.side_effect = mock_loader_side_effect

    result = pre_commit.get_configuration("RadLang")

    assert "arg_a" in result.config_data["repos"][0]["hooks"][0]["args"]
    assert "value_a" in result.config_data["repos"][0]["hooks"][0]["args"]


def test_that_pre_commit_calculates_a_serializable_hook_configuration(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
):
    def mock_loader_side_effect(resource):
        # Language config file
        return """
        repos:
        -   repo: http://sample-repo.com/hooks
            rev: 1.0.25
            hooks:
            -    id: hook-a
            -    id: hook-b
        """

    mock_data_loader.side_effect = mock_loader_side_effect

    hook_configuration = pre_commit.get_serialized_configuration("RadLang")

    assert len(hook_configuration.repos) == 1
    assert hook_configuration.repos[0].revision == "1.0.25"
    assert len(hook_configuration.repos[0].hooks) == 2
    assert "hook-a" in hook_configuration.repos[0].hooks


# def test_that_pre_commit_excludes_files_in_specific_hooks(
#     language_support_service: LanguageSupportService,
#     mock_data_loader: MagicMock,
#     mock_hashlib: MagicMock,
# ):
#     def mock_loader_side_effect(resource):
#         # Language config file
#         return """
#         repos:
#         -   repo: http://example-repo.com/
#             rev: 1.0.25
#             hooks:
#             -    id: hook-id
#             -    id: hook-id-2
#         """

#     language_support_service.pre_commit_settings.repos[0].hooks[0].exclude_file_patterns = [
#         "file_a.py"
#     ]
#     mock_data_loader.side_effect = mock_loader_side_effect

#     pre_commit.version_for_language("RadLang")

#     pre_commit.pre_commit_settings.repos[0].hooks[0].exclude_file_patterns = []

#     pre_commit.version_for_language("RadLang")

#     assert mock_hashlib.md5.call_count == 2
#     call_1_config, _ = mock_hashlib.md5.call_args_list[0]
#     call_2_config, _ = mock_hashlib.md5.call_args_list[1]

#     assert "file_a" in str(call_1_config)
#     assert "file_a" not in str(call_2_config)


def test_that_pre_commit_suppresses_hooks_in_repo(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    mock_hashlib: MagicMock,
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

    pre_commit.pre_commit_settings.repos[0].suppressed_hook_ids = ["hook-id-2"]
    mock_data_loader.side_effect = mock_loader_side_effect

    result = pre_commit.get_configuration("RadLang")

    assert "hook-id-2" not in result
    assert "hook-id" == result.config_data["repos"][0]["hooks"][0]["id"]


def test_that_pre_commit_removes_repo_when_all_hooks_suppressed(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    mock_hashlib: MagicMock,
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

    pre_commit.pre_commit_settings.repos[0].suppressed_hook_ids = [
        "hook-id",
        "hook-id-2",
    ]
    mock_data_loader.side_effect = mock_loader_side_effect

    result = pre_commit.get_configuration("RadLang")

    assert "http://example-repo.com/" not in result


def test_that_pre_commit_removes_the_one_hook_multiple_times_without_a_problem(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    mock_hashlib: MagicMock,
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

    pre_commit.pre_commit_settings.repos[0].suppressed_hook_ids = [
        "hook-id",
        "hook-id",
    ]
    mock_data_loader.side_effect = mock_loader_side_effect

    result = pre_commit.get_configuration("RadLang")

    assert "hook-id" not in result


def test_that_pre_commit_removes_repo_when_repo_suppressed(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    mock_hashlib: MagicMock,
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

    pre_commit.pre_commit_settings.suppressed_repos = ["http://example-repo.com/"]
    mock_data_loader.side_effect = mock_loader_side_effect

    result = pre_commit.get_configuration("RadLang")

    assert "http://example-repo.com/" not in result


#### _load_language_config_files ####
def test_that_pre_commit_langauge_config_gets_loaded(
    pre_commit: PreCommitAbstraction,
):
    result = pre_commit._load_language_config_file("JavaScript")

    assert result.success


def test_that_pre_commit_language_config_does_not_get_loaded(
    pre_commit: PreCommitAbstraction,
):
    result = pre_commit._load_language_config_file("RadLang")

    assert not result.success


#### _install_pre_commit_configs ####
# def test_that_pre_commit_language_config_gets_installed(
#     pre_commit: PreCommitAbstraction, mock_subprocess: MagicMock
# ):
#     result = pre_commit._install_pre_commit_configs("JavaScript")

#     mock_subprocess.run.assert_called_with(["pre-commit", "install-language-config"])

#     assert result.num_successful > 0
#     assert result.num_non_success == 0
#     assert len(result.non_success_messages) == 0


def test_that_pre_commit_language_config_does_not_get_installed(
    pre_commit: PreCommitAbstraction, mock_subprocess: MagicMock
):
    result = pre_commit._install_pre_commit_configs("RadLang")

    assert not mock_subprocess.called

    assert result.num_non_success == 0
    assert result.num_successful == 0
    assert len(result.non_success_messages) == 0


# def test_that_pre_commit_install_captures_error_if_cannot_install_config(
#     pre_commit: PreCommitAbstraction, mock_subprocess: MagicMock
# ):
#     mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)

#     result = pre_commit._install_pre_commit_configs("JavaScript")

#     assert result.num_successful == 0
#     assert result.num_non_success > 0

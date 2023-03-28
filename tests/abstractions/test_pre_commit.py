from subprocess import CompletedProcess
from unittest.mock import MagicMock

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
    mock_open: MagicMock,
):
    mock_data_loader.return_value = "yaml: data"
    pre_commit.ignored_file_patterns = ["mock_pattern"]
    pre_commit.install("Python")

    assert (
        "exclude: mock_pattern"
        in mock_open.return_value.write.call_args_list[0].args[0]
    )


def test_that_pre_commit_templates_are_loaded_without_exclude(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    mock_open: MagicMock,
):
    mock_data_loader.return_value = "yaml: data"
    pre_commit.ignored_file_patterns = []
    pre_commit.install("Python")

    assert "exclude:" not in mock_open.return_value.write.call_args_list[0].args[0]


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
    pre_commit.install("Python")

    assert (
        "exclude: ^(mock_pattern1|mock_pattern2)"
        in mock_open.return_value.write.call_args_list[0].args[0]
    )


def test_that_version_identifiers_are_calculated_for_known_languages(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    version = pre_commit.version_for_language("Python")

    assert version == "mock-hash-code"


def test_that_pre_commit_treats_missing_templates_as_unsupported_language(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    mock_subprocess: MagicMock,
):
    mock_data_loader.side_effect = ValueError
    with pytest.raises(LanguageNotSupportedError):
        pre_commit.install("BadLang")


def test_that_pre_commit_treats_missing_templates_as_unsupported_language_when_checking_versions(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    mock_subprocess: MagicMock,
):
    mock_data_loader.side_effect = ValueError
    with pytest.raises(LanguageNotSupportedError):
        pre_commit.version_for_language("BadLang")


def test_that_pre_commit_treats_failing_process_as_install_failed_error(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    with pytest.raises(InstallFailedError):
        pre_commit.install("Python")


def test_that_pre_commit_executes_hooks_successfully(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.execute_hooks()

    assert execute_result.successful
    assert "--all-files" not in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_executes_hooks_successfully_including_all_files(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.execute_hooks(all_files=True)

    assert execute_result.successful
    assert "--all-files" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_executes_hooks_and_reports_failures(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    execute_result = pre_commit.execute_hooks()

    assert not execute_result.successful


def test_that_pre_commit_executes_a_single_hook_if_specified(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    pre_commit.execute_hooks(hook_id="detect-secrets")

    assert mock_subprocess.run.call_args_list[0].args[0][-1] == "detect-secrets"


def test_that_pre_commit_identifies_a_security_hook_we_can_use_during_init(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
):
    def mock_loader_side_effect(resource):
        if resource == "secrets_detecting_repos.yaml":
            # Secrets detection repo/hooks resource
            return """
                http://sample-repo.com/baddie-finder:
                    - baddie-finder-hook
            """
        else:
            # Language config file
            return """
            repos:
            -   repo: http://sample-repo.com/baddie-finder
                hooks:
                -    id: baddie-finder-hook
            """

    mock_data_loader.side_effect = mock_loader_side_effect

    hook_id = pre_commit.secret_detection_hook_id("Python")

    assert hook_id == "baddie-finder-hook"


def test_that_pre_commit_overrides_arguments_in_a_security_hook(
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
    pre_commit.pre_commit_settings.repos[0].hooks[0].arguments = [
        "arg_a",
        "value_a",
    ]

    mock_data_loader.side_effect = mock_loader_side_effect

    pre_commit.install("RadLang")

    assert "arg_a" in mock_open.return_value.write.call_args_list[0].args[0]
    assert "value_a" in mock_open.return_value.write.call_args_list[0].args[0]
    # Assert the original argument was removed
    assert "orig_arg" not in mock_open.return_value.write.call_args_list[0].args[0]


def test_that_pre_commit_overrides_arguments_do_not_apply_to_a_different_hook_id(
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
    pre_commit.pre_commit_settings.repos[0].hooks[
        0
    ].id = "goodie-finder-hook"  # doesn't match
    pre_commit.pre_commit_settings.repos[0].hooks[0].arguments = [
        "arg_a",
        "value_a",
    ]

    mock_data_loader.side_effect = mock_loader_side_effect

    pre_commit.install("RadLang")

    assert "arg_a" not in mock_open.return_value.write.call_args_list[0].args[0]
    assert "value_a" not in mock_open.return_value.write.call_args_list[0].args[0]
    # assert the original arg was left in place
    assert "orig_arg" in mock_open.return_value.write.call_args_list[0].args[0]


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

    pre_commit.install("RadLang")

    assert "arg_a" in mock_open.return_value.write.call_args_list[0].args[0]
    assert "value_a" in mock_open.return_value.write.call_args_list[0].args[0]
    # assert the original arg was left in place
    assert "orig_arg" in mock_open.return_value.write.call_args_list[0].args[0]


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

    pre_commit.install("RadLang")

    assert "arg_a" in mock_open.return_value.write.call_args_list[0].args[0]
    assert "value_a" in mock_open.return_value.write.call_args_list[0].args[0]


def test_that_pre_commit_does_not_identify_a_security_hook_if_config_does_not_use_repo_even_if_hook_id_matches(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
):
    def mock_loader_side_effect(resource):
        if resource == "secrets_detecting_repos.yaml":
            # Secrets detection repo/hooks resource
            return """
                http://sample-repo.com/baddie-finder:
                    - baddie-finder-hook
            """
        else:
            # Language config file
            return """
            repos:
            -   repo: http://sample-repo.com/goodie-finder # does not match our secrets_detectors
                hooks:
                -    id: baddie-finder-hook
            """

    mock_data_loader.side_effect = mock_loader_side_effect

    hook_id = pre_commit.secret_detection_hook_id("Python")

    assert hook_id is None


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

    hook_configuration = pre_commit.get_configuration("RadLang")

    assert len(hook_configuration.repos) == 1
    assert hook_configuration.repos[0].revision == "1.0.25"
    assert len(hook_configuration.repos[0].hooks) == 2
    assert "hook-a" in hook_configuration.repos[0].hooks


def test_that_pre_commit_excludes_files_in_specific_hooks(
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

    pre_commit.pre_commit_settings.repos[0].hooks[0].exclude_file_patterns = [
        "file_a.py"
    ]
    mock_data_loader.side_effect = mock_loader_side_effect

    pre_commit.version_for_language("RadLang")

    pre_commit.pre_commit_settings.repos[0].hooks[0].exclude_file_patterns = []

    pre_commit.version_for_language("RadLang")

    assert mock_hashlib.md5.call_count == 2
    call_1_config, _ = mock_hashlib.md5.call_args_list[0]
    call_2_config, _ = mock_hashlib.md5.call_args_list[1]

    assert "file_a" in str(call_1_config)
    assert "file_a" not in str(call_2_config)


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

    pre_commit.version_for_language("RadLang")

    assert mock_hashlib.md5.call_count == 1
    call_1_config, _ = mock_hashlib.md5.call_args_list[0]

    assert "hook-id-2" not in str(call_1_config)
    assert "hook-id" in str(call_1_config)


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

    pre_commit.version_for_language("RadLang")

    assert mock_hashlib.md5.call_count == 1
    call_1_config, _ = mock_hashlib.md5.call_args_list[0]

    assert "http://example-repo.com/" not in str(call_1_config)


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

    pre_commit.version_for_language("RadLang")

    assert mock_hashlib.md5.call_count == 1
    call_1_config, _ = mock_hashlib.md5.call_args_list[0]

    assert "hook-id" not in str(call_1_config)


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

    pre_commit.version_for_language("RadLang")

    assert mock_hashlib.md5.call_count == 1
    call_1_config, _ = mock_hashlib.md5.call_args_list[0]

    assert "http://example-repo.com/" not in str(call_1_config)


def test_that_pre_commit_does_not_identify_a_security_hook_if_config_uses_matching_repo_but_not_matching_hook(
    pre_commit: PreCommitAbstraction,
    mock_data_loader: MagicMock,
):
    def mock_loader_side_effect(resource):
        if resource == "secrets_detecting_repos.yaml":
            # Secrets detection repo/hooks resource
            return """
                http://sample-repo.com/baddie-finder:
                    - baddie-finder-hook
            """
        else:
            # Language config file
            return """
            repos:
            -   repo: http://sample-repo.com/baddie-finder
                hooks:
                -    id: goodie-finder-hook # does not match our secrets_detectors
            """

    mock_data_loader.side_effect = mock_loader_side_effect

    hook_id = pre_commit.secret_detection_hook_id("Python")

    assert hook_id is None


def test_that_get_current_config_returns_config_data(
    pre_commit: PreCommitAbstraction, mock_open_config: MagicMock
):
    config = pre_commit.get_current_configuration()

    assert config["exclude"] == "some-exclude-regex"


##### validate_config #####
def test_that_validate_config_returns_no_output_on_config_match(
    pre_commit: PreCommitAbstraction,
    mock_hashlib: MagicMock,
    mock_data_loader: MagicMock,
):
    validation_result = pre_commit.validate_config("Python")

    assert validation_result.successful
    assert validation_result.output == ""


def test_that_validate_config_detects_mismatched_configs(
    pre_commit: PreCommitAbstraction,
    mock_hashlib_no_match: MagicMock,
    mock_data_loader: MagicMock,
    mock_open_config: MagicMock,
):
    mock_data_loader.return_value = '{"exclude": "some-exclude-regex","repos":[{"hooks":[{"id":"some-test-hook"}],"repo":"xyz://some-test-repo-url","rev":"1.0.1"}]}'
    validation_result = pre_commit.validate_config("Python")

    assert not validation_result.successful


def test_that_validate_config_detects_mismatched_hook_versions(
    pre_commit: PreCommitAbstraction,
    mock_hashlib_no_match: MagicMock,
    mock_data_loader: MagicMock,
    mock_open_config: MagicMock,
):
    load_return_value = """
    exclude: some-exclude-regex
    repos:
    - hooks:
      - id: some-test-hook
      repo: xyz://some-test-repo-url
      rev: 1.0.1
    - hooks:
      - id: some-other-test-hook
      repo: xyz://some-other-test-repo-url
      rev: 1.0.0
    """
    mock_data_loader.return_value = load_return_value
    validation_result = pre_commit.validate_config("Python")
    output_by_line = validation_result.output.splitlines()

    assert (
        output_by_line[-1]
        == "Expected xyz://some-test-repo-url to be rev 1.0.1 but it is configured to rev 1.0.0"
    )


def test_that_validate_config_detects_extra_repos(
    pre_commit: PreCommitAbstraction,
    mock_hashlib_no_match: MagicMock,
    mock_data_loader: MagicMock,
    mock_open_config: MagicMock,
):
    load_return_value = """
    exclude: some-exclude-regex
    repos:
    - hooks:
      - id: some-test-hook
      repo: xyz://some-test-repo-url
      rev: 1.0.0
    """
    mock_data_loader.return_value = load_return_value
    validation_result = pre_commit.validate_config("Python")
    output_by_line = validation_result.output.splitlines()

    assert output_by_line[-3] == "Found unexpected repos in .pre-commit-config.yaml:"
    assert output_by_line[-2] == "- xyz://some-other-test-repo-url"


def test_that_validate_config_detects_missing_repos(
    pre_commit: PreCommitAbstraction,
    mock_hashlib_no_match: MagicMock,
    mock_data_loader: MagicMock,
    mock_open_config: MagicMock,
):
    load_return_value = """
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
    - hooks:
      - id: some-third-test-hook
      repo: xyz://some-third-test-repo-url
      rev: 1.0.0
    """
    mock_data_loader.return_value = load_return_value
    validation_result = pre_commit.validate_config("Python")
    output_by_line = validation_result.output.splitlines()

    assert (
        output_by_line[-4]
        == "Some expected repos were misssing from .pre-commit-config.yaml:"
    )
    assert output_by_line[-3] == "- xyz://some-third-test-repo-url"


##### autoupdate_hooks #####
def test_that_pre_commit_autoupdate_hooks_executes_successfully(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.autoupdate_hooks()

    assert execute_result.successful


def test_that_pre_commit_autoupdate_hooks_properly_handles_failed_executions(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    execute_result = pre_commit.autoupdate_hooks()

    assert not execute_result.successful


def test_that_pre_commit_autoupdate_hooks_executes_successfully_with_bleeding_edge(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.autoupdate_hooks(bleeding_edge=True)

    assert execute_result.successful
    assert "--bleeding-edge" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_autoupdate_hooks_executes_successfully_with_freeze(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.autoupdate_hooks(freeze=True)

    assert execute_result.successful
    assert "--freeze" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_autoupdate_hooks_executes_successfully_with_repos(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    test_repos = ["some-repo-url"]
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.autoupdate_hooks(repos=test_repos)

    assert execute_result.successful
    assert "--repo some-repo-url" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_autoupdate_hooks_executes_successfully_with_multiple_repos(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    test_repos = ["some-repo-url", "some-other-repo-url"]
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.autoupdate_hooks(repos=test_repos)

    assert execute_result.successful
    assert "--repo some-repo-url" in mock_subprocess.run.call_args_list[0].args[0]
    assert "--repo some-other-repo-url" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_autoupdate_hooks_fails_with_repos_containing_non_strings(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    test_repos = [{"something": "something-else"}]
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.autoupdate_hooks(repos=test_repos)

    assert not execute_result.successful


def test_that_pre_commit_autoupdate_hooks_ignores_repos_when_repos_is_a_dict(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    test_repos = {}
    test_repos_string = "string"
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.autoupdate_hooks(repos=test_repos)

    assert execute_result.successful
    assert "--repo {}" not in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_autoupdate_hooks_converts_repos_when_repos_is_a_string(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    test_repos = "string"
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.autoupdate_hooks(repos=test_repos)

    assert execute_result.successful
    assert "--repo string" in mock_subprocess.run.call_args_list[0].args[0]


##### update #####
def test_that_pre_commit_update_executes_successfully(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.update()

    assert execute_result.successful


def test_that_pre_commit_update_properly_handles_failed_executions(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    execute_result = pre_commit.update()

    assert not execute_result.successful


##### remove_unused_hooks #####
def test_that_pre_commit_remove_unused_hookss_executes_successfully(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = pre_commit.remove_unused_hooks()

    assert execute_result.successful


def test_that_pre_commit_remove_unused_hooks_properly_handles_failed_executions(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    execute_result = pre_commit.remove_unused_hooks()

    assert not execute_result.successful

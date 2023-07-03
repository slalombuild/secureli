from unittest.mock import MagicMock
from subprocess import CompletedProcess

import pytest
from pytest_mock import MockerFixture

from secureli.abstractions.pre_commit import (
    InstallResult,
    LanguagePreCommitConfigInstallResult,
    GetPreCommitResult,
    LanguageNotSupportedError,
    HookConfiguration,
    Repo,
)
from secureli.services.language_support import (
    LanguageSupportService,
    InstallFailedException,
)


@pytest.fixture()
def mock_subprocess(mocker: MockerFixture) -> MagicMock:
    mock_subprocess = MagicMock()
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    mocker.patch("secureli.services.language_support.subprocess", mock_subprocess)
    return mock_subprocess


@pytest.fixture()
def mock_hashlib(mocker: MockerFixture) -> MagicMock:
    mock_hashlib = MagicMock()
    mock_md5 = MagicMock()
    mock_hashlib.md5.return_value = mock_md5
    mock_md5.hexdigest.return_value = "mock-hash-code"
    mocker.patch("secureli.services.language_support.hashlib", mock_hashlib)
    return mock_hashlib


@pytest.fixture()
def mock_hashlib_no_match(mocker: MockerFixture) -> MagicMock:
    mock_hashlib = MagicMock()
    mock_md5 = MagicMock()
    mock_hashlib.md5.return_value = mock_md5
    mock_md5.hexdigest.side_effect = ["first-hash-code", "second-hash-code"]
    mocker.patch("secureli.services.language_support.hashlib", mock_hashlib)
    return mock_hashlib


# simulate open current .pre-commit-config.yaml for sample repo
@pytest.fixture()
def mock_open_config(mocker: MockerFixture) -> MagicMock:
    mock_open = mocker.mock_open(
        read_data="""
    exclude: some-exclude-regex
    repos:
    - hooks:
      - id: some-test-hook
      repo: http://sample-repo.com/baddie-finder
      rev: 1.0.0
    - hooks:
      - id: some-other-test-hook
      repo: xyz://some-other-test-repo-url
      rev: 1.0.0
    """
    )
    mocker.patch("builtins.open", mock_open)


@pytest.fixture()
def mock_pre_commit_hook() -> MagicMock:
    mock_pre_commit_config_install_result = LanguagePreCommitConfigInstallResult(
        num_successful=0, num_non_success=0, non_success_messages=list()
    )

    mock_pre_commit_hook = MagicMock()
    # mock_pre_commit_hook.version_for_language.return_value = "abc123"
    mock_pre_commit_hook.install.return_value = InstallResult(
        successful=True,
        # version_installed="abc123",
        # configs_result=mock_pre_commit_config_install_result,
    )
    # mock_pre_commit_hook.secret_detection_hook_id.return_value = "baddie-finder"

    # mock the calling of most current version of available pre-commit-config file
    mock_pre_commit_hook.get_secret_detecting_repos.return_value = {
        "http://sample-repo.com/baddie-finder": ["baddie-finder-hook"]
    }
    return mock_pre_commit_hook


@pytest.fixture()
def mock_git_ignore() -> MagicMock:
    mock_git_ignore = MagicMock()
    return mock_git_ignore


@pytest.fixture()
def language_support_service(
    mock_pre_commit_hook: MagicMock,
    mock_git_ignore: MagicMock,
) -> LanguageSupportService:
    return LanguageSupportService(
        pre_commit_hook=mock_pre_commit_hook,
        git_ignore=mock_git_ignore,
    )


#### secret_detection_hook ####
def test_that_language_support_identifies_a_security_hook_we_can_use_during_init(
    language_support_service: LanguageSupportService, mock_pre_commit_hook: MagicMock
):
    mock_pre_commit_hook.get_configuration.return_value = GetPreCommitResult(
        successful=True,
        config_data={
            "repos": [
                {
                    "repo": "http://sample-repo.com/baddie-finder",
                    "rev": "1.0.3",
                    "hooks": [{"id": "baddie-finder-hook"}],
                }
            ]
        },
    )

    hook_id = language_support_service.secret_detection_hook_id(["Python"])

    assert hook_id == "baddie-finder-hook"


def test_that_language_support_does_not_identify_a_security_hook_if_config_does_not_use_repo_even_if_hook_id_matches(
    language_support_service: LanguageSupportService, mock_pre_commit_hook: MagicMock
):
    mock_pre_commit_hook.get_configuration.return_value = GetPreCommitResult(
        successful=True,
        config_data={
            "repos": [
                {
                    "repo": "http://sample-repo.com/baddie-finder",
                    "rev": "1.0.3",
                    "hooks": [{"id": "baddie-finder-hook"}],
                }
            ]
        },
    )

    # hook does not match config hook
    mock_pre_commit_hook.get_secret_detecting_repos.return_value = {
        "http://sample-repo.com/baddie-finder": ["baddie-hook-finder"]
    }

    hook_id = language_support_service.secret_detection_hook_id(["Python"])

    assert hook_id is None


def test_that_language_support_does_not_identify_a_security_hook_if_config_uses_matching_repo_but_not_matching_hook(
    language_support_service: LanguageSupportService, mock_pre_commit_hook: MagicMock
):
    mock_pre_commit_hook.get_configuration.return_value = GetPreCommitResult(
        successful=True,
        config_data={
            "repos": [
                {
                    "repo": "http://sample-repo.com/baddie-finder",
                    "rev": "1.0.3",
                    "hooks": [{"id": "baddie-finder-hook"}],
                }
            ]
        },
    )

    # repo url does not match config url
    mock_pre_commit_hook.get_secret_detecting_repos.return_value = {
        "http://sample-repo.com/baddie-finder-wrong": ["baddie-finder-hook"]
    }

    hook_id = language_support_service.secret_detection_hook_id(["Python"])

    assert hook_id is None


#### apply_support ####
def test_that_language_support_attempts_to_install_pre_commit_hooks(
    language_support_service: LanguageSupportService,
    mock_pre_commit_hook: MagicMock,
    mock_open: MagicMock,
):
    mock_pre_commit_hook.get_configuration.return_value = GetPreCommitResult(
        successful=True,
        config_data={
            "repos": [
                {
                    "repo": "http://sample-repo.com/baddie-finder",
                    "rev": "1.0.2",
                    "hooks": [{"id": "baddie-finder-hook"}],
                }
            ]
        },
    )

    metadata = language_support_service.apply_support(["RadLang"])

    mock_pre_commit_hook.get_configuration.assert_called()
    assert metadata.security_hook_id == "baddie-finder-hook"


def test_that_language_support_fails_if_config_is_unsuccessful(
    language_support_service: LanguageSupportService,
    mock_pre_commit_hook: MagicMock,
    mock_open: MagicMock,
):
    mock_pre_commit_hook.get_configuration.return_value = GetPreCommitResult(
        successful=False, config_data={}
    )

    with pytest.raises(InstallFailedException):
        language_support_service.apply_support(["radLang", "lameLang"])


#### version_for_language ####
def test_that_language_support_calculates_version_for_language(
    language_support_service: LanguageSupportService,
    mock_pre_commit_hook: MagicMock,
):
    version = language_support_service.version_for_language(["RadLang"])

    assert version != None


#### _build_pre_commit_config ####
def test_that_unsopported_language_raises_LanguageNotSupportedError(
    language_support_service: LanguageSupportService, mock_pre_commit_hook: MagicMock
):
    mock_pre_commit_hook._get_language_config.side_effect = LanguageNotSupportedError(
        "BadLang"
    )

    with pytest.raises(LanguageNotSupportedError):
        mock_pre_commit_hook._get_language_config("BadLang")
        language_support_service._build_pre_commit_config(["BadLang"])


#### execute_hooks ####
def test_that_language_support_executes_hooks_successfully(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = language_support_service.execute_hooks()

    assert execute_result.successful
    assert "--all-files" not in mock_subprocess.run.call_args_list[0].args[0]


def test_that_language_support_executes_hooks_successfully_including_all_files(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = language_support_service.execute_hooks(all_files=True)

    assert execute_result.successful
    assert "--all-files" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_language_support_executes_hooks_and_reports_failures(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    execute_result = language_support_service.execute_hooks()

    assert not execute_result.successful


def test_that_language_support_executes_a_single_hook_if_specified(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    language_support_service.execute_hooks(hook_id="detect-secrets")

    assert mock_subprocess.run.call_args_list[0].args[0][-1] == "detect-secrets"


#### _get_current_config ####
def test_that_language_support_gets_current_config_returns_config_data(
    language_support_service: LanguageSupportService, mock_open_config: MagicMock
):
    config = language_support_service._get_current_configuration()

    assert config["exclude"] == "some-exclude-regex"


##### validate_config #####
def test_that_validate_config_returns_no_output_on_config_match(
    language_support_service: LanguageSupportService,
    mock_hashlib: MagicMock,
):
    validation_result = language_support_service.validate_config(["Python"])

    assert validation_result.successful
    assert validation_result.output == ""


def test_that_validate_config_detects_mismatched_configs(
    language_support_service: LanguageSupportService,
    mock_hashlib_no_match: MagicMock,
    mock_open_config: MagicMock,
):
    validation_result = language_support_service.validate_config(["Python"])

    assert not validation_result.successful


def test_that_validate_config_detects_mismatched_hook_versions(
    language_support_service: LanguageSupportService,
    mock_hashlib_no_match: MagicMock,
    mock_open_config: MagicMock,
    mock_pre_commit_hook: MagicMock,
):
    mock_pre_commit_hook.get_configuration.return_value = GetPreCommitResult(
        successful=True,
        config_data={
            "repos": [
                {
                    "repo": "http://sample-repo.com/baddie-finder",
                    "rev": "1.0.1",
                    "hooks": [{"id": "baddie-finder-hook"}],
                }
            ]
        },
    )

    # mock_data_loader.return_value = load_return_value
    validation_result = language_support_service.validate_config(["Python"])
    output_by_line = validation_result.output.splitlines()

    assert (
        output_by_line[-1]
        == "Expected http://sample-repo.com/baddie-finder to be rev 1.0.1 but it is configured to rev 1.0.0"
    )


def test_that_validate_config_works_with_local_repos_that_do_not_have_revs(
    language_support_service: LanguageSupportService,
    mock_pre_commit_hook: MagicMock,
    mock_hashlib_no_match: MagicMock,
    mock_open_config: MagicMock,
):
    mock_pre_commit_hook.get_configuration.return_value = GetPreCommitResult(
        successful=True,
        config_data={
            "repos": [
                {
                    "repo": "local",
                    "hooks": [{"id": "local hook"}],
                }
            ]
        },
    )

    validation_result = language_support_service.validate_config(["Python"])
    assert "Expected local" not in validation_result.output


def test_that_validate_config_detects_extra_repos(
    language_support_service: LanguageSupportService,
    mock_hashlib_no_match: MagicMock,
    mock_open_config: MagicMock,
    mock_pre_commit_hook: MagicMock,
):
    # mock the calling of most current version of available pre-commit-config file
    mock_pre_commit_hook.get_configuration.return_value = GetPreCommitResult(
        successful=True, config_data={"repos": []}
    )
    validation_result = language_support_service.validate_config(["Python"])
    output_by_line = validation_result.output.splitlines()

    assert output_by_line[-4] == "Found unexpected repos in .pre-commit-config.yaml:"
    assert output_by_line[-3] == "- http://sample-repo.com/baddie-finder"


def test_that_validate_config_detects_missing_repos(
    language_support_service: LanguageSupportService,
    mock_hashlib_no_match: MagicMock,
    mock_open_config: MagicMock,
    mock_pre_commit_hook: MagicMock,
):
    mock_pre_commit_hook.get_configuration.return_value = GetPreCommitResult(
        successful=True,
        config_data={
            "repos": [
                {
                    "repo": "xyz://some-test-repo-url",
                    "rev": "1.0.0",
                    "hooks": [{"id": "some-hook"}],
                },
                {
                    "repo": "xyz://some-other-test-repo-url",
                    "rev": "1.0.0",
                    "hooks": [{"id": "some-other-hook"}],
                },
                {
                    "repo": "xyz://some-third-test-repo-url",
                    "rev": "1.0.0",
                    "hooks": [{"id": "some-third-hook"}],
                },
                {
                    "repo": "http://sample-repo.com/baddie-finder",
                    "rev": "1.0.0",
                    "hooks": [{"id": "some-test-hook"}],
                },
            ]
        },
    )
    validation_result = language_support_service.validate_config(["Python"])
    output_by_line = validation_result.output.splitlines()

    assert (
        output_by_line[-8]
        == "Some expected repos were misssing from .pre-commit-config.yaml:"
    )
    assert output_by_line[-6] == "- xyz://some-third-test-repo-url"


##### autoupdate_hooks #####
def test_that_language_support_autoupdate_hooks_executes_successfully(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = language_support_service.autoupdate_hooks()

    assert execute_result.successful


def test_that_language_support_autoupdate_hooks_properly_handles_failed_executions(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    execute_result = language_support_service.autoupdate_hooks()

    assert not execute_result.successful


def test_that_language_support_autoupdate_hooks_executes_successfully_with_bleeding_edge(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = language_support_service.autoupdate_hooks(bleeding_edge=True)

    assert execute_result.successful
    assert "--bleeding-edge" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_language_support_autoupdate_hooks_executes_successfully_with_freeze(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = language_support_service.autoupdate_hooks(freeze=True)

    assert execute_result.successful
    assert "--freeze" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_language_support_autoupdate_hooks_executes_successfully_with_repos(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    test_repos = ["some-repo-url"]
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = language_support_service.autoupdate_hooks(repos=test_repos)

    assert execute_result.successful
    assert "--repo some-repo-url" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_language_support_autoupdate_hooks_executes_successfully_with_multiple_repos(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    test_repos = ["some-repo-url", "some-other-repo-url"]
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = language_support_service.autoupdate_hooks(repos=test_repos)

    assert execute_result.successful
    assert "--repo some-repo-url" in mock_subprocess.run.call_args_list[0].args[0]
    assert "--repo some-other-repo-url" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_language_support_autoupdate_hooks_fails_with_repos_containing_non_strings(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    test_repos = [{"something": "something-else"}]
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = language_support_service.autoupdate_hooks(repos=test_repos)

    assert not execute_result.successful


def test_that_language_support_autoupdate_hooks_ignores_repos_when_repos_is_a_dict(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    test_repos = {}
    test_repos_string = "string"
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = language_support_service.autoupdate_hooks(repos=test_repos)

    assert execute_result.successful
    assert "--repo {}" not in mock_subprocess.run.call_args_list[0].args[0]


def test_that_language_support_autoupdate_hooks_converts_repos_when_repos_is_a_string(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    test_repos = "string"
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = language_support_service.autoupdate_hooks(repos=test_repos)

    assert execute_result.successful
    assert "--repo string" in mock_subprocess.run.call_args_list[0].args[0]


##### update #####
def test_that_language_support_update_executes_successfully(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = language_support_service.update()

    assert execute_result.successful


def test_that_language_support_update_properly_handles_failed_executions(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    execute_result = language_support_service.update()

    assert not execute_result.successful


##### remove_unused_hooks #####
def test_that_language_support_remove_unused_hookss_executes_successfully(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    execute_result = language_support_service.remove_unused_hooks()

    assert execute_result.successful


def test_that_language_support_remove_unused_hooks_properly_handles_failed_executions(
    language_support_service: LanguageSupportService,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    execute_result = language_support_service.remove_unused_hooks()

    assert not execute_result.successful


##### get_serialized_config ####
def test_that_language_support_builds_serializable_config_for_multiple_languages(
    language_support_service: LanguageSupportService, mock_pre_commit_hook: MagicMock
):
    mock_pre_commit_hook.get_serialized_configuration.return_value = HookConfiguration(
        repos=[Repo(repo="http://example/repo.com", revision="1.0.0", hooks=["hook_1"])]
    )

    result = language_support_service.get_serialized_config(["RadLang", "CoolLag"])

    assert len(result) == 2

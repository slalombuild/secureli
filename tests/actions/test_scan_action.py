from pathlib import Path
from secureli.modules.shared.abstractions.pre_commit import RevisionPair
from secureli.actions.action import ActionDependencies
from secureli.actions.scan import ScanAction
from secureli.modules.shared.models.echo import Level
from secureli.modules.shared.models.exit_codes import ExitCode
from secureli.modules.shared.models.install import VerifyOutcome
from secureli.modules.shared.models.language import AnalyzeResult
from secureli.modules.shared.models.logging import LogAction
from secureli.modules.shared.models.publish_results import PublishResultsOption
import secureli.modules.shared.models.repository as RepositoryModels
import secureli.modules.shared.models.config as ConfigModels
from secureli.modules.shared.models.result import Result
from secureli.modules.shared.models.scan import ScanMode, ScanResult
from secureli.repositories import repo_settings
from unittest import mock
from unittest.mock import MagicMock, patch
from pytest_mock import MockerFixture

import os
import pytest

from secureli.settings import Settings

test_folder_path = Path("does-not-matter")


@pytest.fixture()
def mock_hooks_scanner(mock_pre_commit) -> MagicMock:
    mock_hooks_scanner = MagicMock()
    mock_hooks_scanner.scan_repo.return_value = ScanResult(successful=True, failures=[])
    mock_hooks_scanner.pre_commit = mock_pre_commit
    return mock_hooks_scanner


@pytest.fixture()
def mock_pre_commit() -> MagicMock:
    mock_pre_commit = MagicMock()
    mock_pre_commit.get_pre_commit_config.return_value = (
        RepositoryModels.PreCommitSettings(
            repos=[
                RepositoryModels.PreCommitRepo(
                    repo="http://example-repo.com/",
                    rev="master",
                    hooks=[
                        RepositoryModels.PreCommitHook(
                            id="hook-id",
                            arguments=None,
                            additional_args=None,
                        )
                    ],
                )
            ]
        )
    )
    mock_pre_commit.check_for_hook_updates.return_value = {}
    return mock_pre_commit


@pytest.fixture()
def mock_custom_scanners() -> MagicMock:
    mock_custom_scanners = MagicMock()
    mock_custom_scanners.scan_repo.return_value = ScanResult(
        successful=True, failures=[]
    )
    return mock_custom_scanners


@pytest.fixture()
def mock_updater() -> MagicMock:
    mock_updater = MagicMock()
    return mock_updater


@pytest.fixture()
def mock_git_repo() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def mock_get_time_near_epoch(mocker: MockerFixture) -> MagicMock:
    return mocker.patch(
        "secureli.actions.scan.time", return_value=1.0
    )  # 1 second after epoch


@pytest.fixture()
def mock_get_time_far_from_epoch(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("secureli.actions.scan.time", return_value=1e6)


@pytest.fixture()
def mock_default_settings(mock_settings_repository: MagicMock) -> MagicMock:
    mock_echo_settings = RepositoryModels.EchoSettings(level=Level.info)
    mock_settings_file = repo_settings.SecureliFile(echo=mock_echo_settings)
    mock_settings_repository.load.return_value = mock_settings_file

    return mock_settings_repository


@pytest.fixture()
def mock_settings_no_scan_patterns(mock_settings_repository: MagicMock) -> MagicMock:
    mock_echo_settings = RepositoryModels.EchoSettings(level=Level.info)
    mock_settings_file = repo_settings.SecureliFile(echo=mock_echo_settings)
    mock_settings_file.scan_patterns = None
    mock_settings_repository.load.return_value = mock_settings_file

    return mock_settings_repository


@pytest.fixture()
def mock_pass_install_verification(
    mock_secureli_config: MagicMock, mock_language_support: MagicMock
):
    mock_secureli_config.load.return_value = ConfigModels.SecureliConfig(
        languages=["RadLang"], version_installed="abc123"
    )
    mock_language_support.version_for_language.return_value = "abc123"


@pytest.fixture()
def action_deps(
    mock_echo: MagicMock,
    mock_language_analyzer: MagicMock,
    mock_language_support: MagicMock,
    mock_hooks_scanner: MagicMock,
    mock_secureli_config: MagicMock,
    mock_settings_repository: MagicMock,
    mock_updater: MagicMock,
    mock_logging_service: MagicMock,
) -> ActionDependencies:
    return ActionDependencies(
        mock_echo,
        mock_language_analyzer,
        mock_language_support,
        mock_hooks_scanner,
        mock_secureli_config,
        mock_settings_repository,
        mock_updater,
        mock_logging_service,
    )


@pytest.fixture()
def scan_action(
    action_deps: ActionDependencies,
    mock_custom_scanners: MagicMock,
    mock_git_repo: MagicMock,
) -> ScanAction:
    return ScanAction(
        action_deps=action_deps,
        hooks_scanner=action_deps.hooks_scanner,
        custom_scanners=mock_custom_scanners,
        git_repo=mock_git_repo,
    )


@pytest.fixture()
def mock_post_log(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("secureli.modules.shared.utilities.post_log")


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_errors_if_not_successful(
    scan_action: ScanAction,
    mock_hooks_scanner: MagicMock,
    mock_custom_scanners: MagicMock,
    mock_secureli_config: MagicMock,
    mock_language_analyzer: MagicMock,
):
    mock_language = "RadLang"
    mock_language_analyzer.analyze.return_value = AnalyzeResult(
        language_proportions={f"{mock_language}": 1.0},
        skipped_files=[],
    )
    mock_custom_scanners.scan_repo.return_value = ScanResult(
        successful=False, output="So much PII", failures=[]
    )
    mock_hooks_scanner.scan_repo.return_value = ScanResult(
        successful=False, output="Bad Error", failures=[]
    )
    mock_secureli_config.load.return_value = ConfigModels.SecureliConfig(
        languages=[mock_language], version_installed="abc123"
    )

    with pytest.raises(SystemExit) as sys_ext_info:
        scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

    assert sys_ext_info.value.code is ExitCode.SCAN_ISSUES_DETECTED.value


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_scans_if_installed(
    scan_action: ScanAction,
    mock_secureli_config: MagicMock,
    mock_language_support: MagicMock,
    mock_custom_scanners: MagicMock,
    mock_language_analyzer: MagicMock,
    mock_settings_no_scan_patterns: MagicMock,
):
    mock_language_analyzer.analyze.return_value = AnalyzeResult(
        language_proportions={"RadLang": 1.0},
        skipped_files=[],
    )
    mock_secureli_config.load.return_value = ConfigModels.SecureliConfig(
        languages=["RadLang"], version_installed="abc123"
    )
    mock_language_support.version_for_language.return_value = "abc123"

    scan_action.scan_repo(
        test_folder_path, ScanMode.STAGED_ONLY, False, None, "detect-secrets"
    )

    mock_custom_scanners.scan_repo.assert_called_once()


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_conducts_all_scans_and_merges_results(
    scan_action: ScanAction,
    mock_secureli_config: MagicMock,
    mock_language_support: MagicMock,
    mock_hooks_scanner: MagicMock,
    mock_custom_scanners: MagicMock,
    mock_language_analyzer: MagicMock,
    mock_echo: MagicMock,
):
    mock_language_analyzer.analyze.return_value = AnalyzeResult(
        language_proportions={"RadLang": 1.0},
        skipped_files=[],
    )
    mock_secureli_config.load.return_value = ConfigModels.SecureliConfig(
        languages=["RadLang"], version_installed="abc123"
    )
    mock_language_support.version_for_language.return_value = "abc123"
    mock_failure_1 = "Hooks scan failure"
    mock_failure_2 = "PII scan failure"
    mock_hooks_scanner.scan_repo.return_value = ScanResult(
        successful=False, failures=[], output=mock_failure_1
    )
    mock_custom_scanners.scan_repo.return_value = ScanResult(
        successful=False, failures=[], output=mock_failure_2
    )

    with pytest.raises(SystemExit):
        scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)
        mock_hooks_scanner.scan_repo.assert_called_once()
        mock_custom_scanners.scan_repo.assert_called_once()
        mock_echo.print.assert_called_once_with(f"\n{mock_failure_1}\n{mock_failure_2}")


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_continue_scan_if_upgrade_canceled(
    scan_action: ScanAction,
    mock_secureli_config: MagicMock,
    mock_language_support: MagicMock,
    mock_hooks_scanner: MagicMock,
    mock_custom_scanners: MagicMock,
    mock_echo: MagicMock,
    mock_language_analyzer: MagicMock,
):
    mock_language_analyzer.analyze.return_value = AnalyzeResult(
        language_proportions={"RadLang": 1.0},
        skipped_files=[],
    )
    mock_secureli_config.load.return_value = ConfigModels.SecureliConfig(
        languages=["RadLang"], version_installed="abc123"
    )
    mock_language_support.version_for_language.return_value = "xyz987"
    mock_echo.confirm.return_value = False

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

    mock_hooks_scanner.scan_repo.assert_called_once()
    mock_custom_scanners.scan_repo.assert_called_once()


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_does_not_scan_if_not_installed(
    scan_action: ScanAction,
    mock_hooks_scanner: MagicMock,
    mock_custom_scanners: MagicMock,
    mock_secureli_config: MagicMock,
    mock_echo: MagicMock,
    mock_language_analyzer: MagicMock,
):
    with patch.object(Path, "exists", return_value=False):
        mock_secureli_config.load.return_value = ConfigModels.SecureliConfig()
        mock_secureli_config.verify.return_value = (
            ConfigModels.VerifyConfigOutcome.UP_TO_DATE
        )
        mock_echo.confirm.return_value = False

        scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

        mock_hooks_scanner.scan_repo.assert_not_called()
        mock_custom_scanners.scan_repo.assert_not_called()


def test_that_scan_checks_for_updates(
    scan_action: ScanAction,
    mock_hooks_scanner: MagicMock,
    mock_secureli_config: MagicMock,
    mock_pass_install_verification: MagicMock,
):
    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, always_yes=True)
    mock_hooks_scanner.pre_commit.check_for_hook_updates.assert_called_once()


def test_that_scan_only_checks_for_updates_periodically(
    scan_action: ScanAction,
    mock_hooks_scanner: MagicMock,
    mock_get_time_near_epoch: MagicMock,
    mock_secureli_config: MagicMock,
):
    mock_secureli_config.load.return_value = ConfigModels.SecureliConfig()

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, always_yes=True)
    mock_hooks_scanner.pre_commit.check_for_hook_updates.assert_not_called()


def test_that_scan_update_check_uses_pre_commit_config(
    scan_action: ScanAction,
    mock_hooks_scanner: MagicMock,
    mock_secureli_config: MagicMock,
):
    mock_secureli_config.load.return_value = ConfigModels.SecureliConfig()
    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, always_yes=True)
    mock_hooks_scanner.pre_commit.get_pre_commit_config.assert_called_once()


# Test that _check_secureli_hook_updates returns UP_TO_DATE if no hooks need updating
def test_scan_update_check_return_value_when_up_to_date(
    scan_action: ScanAction,
    mock_hooks_scanner: MagicMock,
    mock_secureli_config: MagicMock,
):
    mock_secureli_config.load.return_value = ConfigModels.SecureliConfig()
    result = scan_action._check_secureli_hook_updates(test_folder_path)
    assert result.outcome == VerifyOutcome.UP_TO_DATE


# Test that _check_secureli_hook_updates returns UPDATE_CANCELED if hooks need updating
def test_scan_update_check_return_value_when_not_up_to_date(
    scan_action: ScanAction,
    mock_hooks_scanner: MagicMock,
    mock_secureli_config: MagicMock,
):
    mock_secureli_config.load.return_value = ConfigModels.SecureliConfig()
    mock_hooks_scanner.pre_commit.check_for_hook_updates.return_value = {
        "http://example-repo.com/": RevisionPair(oldRev="old-rev", newRev="new-rev")
    }
    result = scan_action._check_secureli_hook_updates(test_folder_path)
    assert result.outcome == VerifyOutcome.UPDATE_CANCELED


# Validate that scan_repo persists changes to the .secureli.yaml file after checking for hook updates
def test_that_scan_update_check_updates_last_check_time(
    scan_action: ScanAction,
    mock_hooks_scanner: MagicMock,
    mock_get_time_far_from_epoch: MagicMock,
    mock_secureli_config: MagicMock,
    mock_pass_install_verification: MagicMock,
):
    mock_secureli_config.load.return_value = ConfigModels.SecureliConfig(
        languages=["RadLang", "BadLang"], version_installed="abc123"
    )
    mock_secureli_config.verify.return_value = (
        ConfigModels.VerifyConfigOutcome.UP_TO_DATE
    )
    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, always_yes=True)
    mock_secureli_config.save.assert_called_once()
    assert mock_secureli_config.save.call_args.args[0].last_hook_update_check == 1e6


def test_publish_results_always(scan_action: ScanAction, mock_post_log: MagicMock):
    mock_post_log.return_value.result = Result.SUCCESS
    mock_post_log.return_value.result_message = "Success"

    scan_action.publish_results(
        PublishResultsOption.ALWAYS,
        action_successful=True,
        log_str="log_str",
    )

    mock_post_log.assert_called_once_with("log_str", Settings())
    scan_action.action_deps.logging.success.assert_called_once_with(LogAction.publish)


def test_publish_results_on_fail_and_action_successful(
    scan_action: ScanAction, mock_post_log: MagicMock
):
    scan_action.publish_results(
        publish_results_condition=PublishResultsOption.ON_FAIL,
        action_successful=True,
        log_str="log_str",
    )

    mock_post_log.assert_not_called()
    scan_action.action_deps.logging.success.assert_not_called()


def test_publish_results_on_fail_and_action_not_successful(
    scan_action: ScanAction, mock_post_log: MagicMock
):
    mock_post_log.return_value.result = Result.FAILURE
    mock_post_log.return_value.result_message = "Failure"

    scan_action.publish_results(
        publish_results_condition=PublishResultsOption.ON_FAIL,
        action_successful=False,
        log_str="log_str",
    )

    mock_post_log.assert_called_once_with("log_str", Settings())
    scan_action.action_deps.logging.failure.assert_called_once_with(
        LogAction.publish, "Failure"
    )


def test_verify_install_is_called_with_commted_files(
    scan_action: ScanAction,
    mock_git_repo: MagicMock,
    mock_secureli_config: MagicMock,
    mock_language_analyzer: MagicMock,
):
    mock_secureli_config.load.return_value = ConfigModels.SecureliConfig(
        languages=["RadLang"], version_installed=1
    )

    mock_files = ["file1.py", "file2.py"]

    mock_git_repo.get_commit_diff.return_value = mock_files
    scan_action.scan_repo(
        folder_path=Path(""),
        scan_mode=ScanMode.STAGED_ONLY,
        always_yes=True,
        publish_results_condition=PublishResultsOption.NEVER,
        specific_test=None,
        files=None,
    )

    mock_language_analyzer.analyze.assert_called_once_with(
        Path("."), [Path(file) for file in mock_files]
    )


def test_verify_install_is_called_with_user_specified_files(
    scan_action: ScanAction,
    mock_git_repo: MagicMock,
    mock_secureli_config: MagicMock,
    mock_language_analyzer: MagicMock,
):
    mock_secureli_config.load.return_value = ConfigModels.SecureliConfig(
        languages=["RadLang"], version_installed=1
    )

    mock_files = ["file1.py", "file2.py"]

    mock_git_repo.get_commit_diff.return_value = None
    scan_action.scan_repo(
        folder_path=Path(""),
        scan_mode=ScanMode.STAGED_ONLY,
        always_yes=True,
        publish_results_condition=PublishResultsOption.NEVER,
        specific_test=None,
        files=mock_files,
    )

    mock_language_analyzer.analyze.assert_called_once_with(
        Path("."), [Path(file) for file in mock_files]
    )


def test_verify_install_is_called_with_no_specified_files(
    scan_action: ScanAction,
    mock_git_repo: MagicMock,
    mock_secureli_config: MagicMock,
    mock_language_analyzer: MagicMock,
):
    mock_secureli_config.load.return_value = ConfigModels.SecureliConfig(
        languages=["RadLang"], version_installed=1
    )

    mock_git_repo.get_commit_diff.return_value = None
    scan_action.scan_repo(
        folder_path=Path(""),
        scan_mode=ScanMode.STAGED_ONLY,
        always_yes=True,
        publish_results_condition=PublishResultsOption.NEVER,
        specific_test=None,
        files=None,
    )

    mock_language_analyzer.analyze.assert_called_once_with(Path("."), None)


def test_get_commited_files_returns_commit_diff(
    scan_action: ScanAction,
    mock_git_repo: MagicMock,
    mock_secureli_config: MagicMock,
):
    mock_secureli_config.load.return_value = ConfigModels.SecureliConfig(
        languages=["RadLang"], version_installed=1
    )
    mock_files = [Path("file1.py"), Path("file2.py")]
    mock_git_repo.get_commit_diff.return_value = mock_files
    result = scan_action._get_commited_files(scan_mode=ScanMode.STAGED_ONLY)
    assert result == mock_files


def test_get_commited_files_returns_none_when_not_installed(
    scan_action: ScanAction,
    mock_secureli_config: MagicMock,
):
    mock_secureli_config.load.return_value = ConfigModels.SecureliConfig(
        languages=[], version_installed=None
    )
    result = scan_action._get_commited_files(scan_mode=ScanMode.STAGED_ONLY)
    assert result is None


def test_get_commited_files_returns_when_scan_mode_is_not_staged_only(
    scan_action: ScanAction,
    mock_secureli_config: MagicMock,
):
    mock_secureli_config.load.return_value = ConfigModels.SecureliConfig(
        languages=["RadLang"], version_installed=1
    )
    result = scan_action._get_commited_files(scan_mode=ScanMode.ALL_FILES)
    assert result is None

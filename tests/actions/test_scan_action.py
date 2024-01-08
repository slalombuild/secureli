from pathlib import Path
from secureli.abstractions.pre_commit import RevisionPair
from secureli.actions.action import ActionDependencies, VerifyOutcome
from secureli.actions.scan import ScanAction
from secureli.repositories.secureli_config import SecureliConfig, VerifyConfigOutcome
from secureli.repositories.settings import (
    PreCommitHook,
    PreCommitRepo,
    PreCommitSettings,
    SecureliFile,
    EchoSettings,
    EchoLevel,
)
from secureli.services.language_analyzer import AnalyzeResult
from secureli.services.scanner import ScanMode, ScanResult, Failure
from unittest import mock
from unittest.mock import MagicMock
from pytest_mock import MockerFixture

import os
import pytest

test_folder_path = Path("does-not-matter")


@pytest.fixture()
def mock_scanner(mock_pre_commit) -> MagicMock:
    mock_scanner = MagicMock()
    mock_scanner.scan_repo.return_value = ScanResult(successful=True, failures=[])
    mock_scanner.pre_commit = mock_pre_commit
    return mock_scanner


@pytest.fixture()
def mock_pre_commit() -> MagicMock:
    mock_pre_commit = MagicMock()
    mock_pre_commit.get_pre_commit_config.return_value = PreCommitSettings(
        repos=[
            PreCommitRepo(
                repo="http://example-repo.com/",
                rev="master",
                hooks=[
                    PreCommitHook(
                        id="hook-id",
                        arguments=None,
                        additional_args=None,
                    )
                ],
            )
        ]
    )
    mock_pre_commit.check_for_hook_updates.return_value = {}
    return mock_pre_commit


@pytest.fixture()
def mock_updater() -> MagicMock:
    mock_updater = MagicMock()
    return mock_updater


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
    mock_echo_settings = EchoSettings(level=EchoLevel.info)
    mock_settings_file = SecureliFile(echo=mock_echo_settings)
    mock_settings_repository.load.return_value = mock_settings_file

    return mock_settings_repository


@pytest.fixture()
def mock_pass_install_verification(
    mock_secureli_config: MagicMock, mock_language_support: MagicMock
):
    mock_secureli_config.load.return_value = SecureliConfig(
        languages=["RadLang"], version_installed="abc123"
    )
    mock_language_support.version_for_language.return_value = "abc123"


@pytest.fixture()
def action_deps(
    mock_echo: MagicMock,
    mock_language_analyzer: MagicMock,
    mock_language_support: MagicMock,
    mock_scanner: MagicMock,
    mock_secureli_config: MagicMock,
    mock_settings_repository: MagicMock,
    mock_updater: MagicMock,
) -> ActionDependencies:
    return ActionDependencies(
        mock_echo,
        mock_language_analyzer,
        mock_language_support,
        mock_scanner,
        mock_secureli_config,
        mock_settings_repository,
        mock_updater,
    )


@pytest.fixture()
def scan_action(
    action_deps: ActionDependencies,
    mock_logging_service: MagicMock,
) -> ScanAction:
    return ScanAction(
        action_deps=action_deps,
        echo=action_deps.echo,
        logging=mock_logging_service,
        scanner=action_deps.scanner,
    )


# @mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
# def test_that_scan_repo_errors_if_not_successful(
#     scan_action: ScanAction,
#     mock_scanner: MagicMock,
#     mock_echo: MagicMock,
# ):
#     mock_scanner.scan_repo.return_value = ScanResult(
#         successful=False, output="Bad Error", failures=[]
#     )
#
#     scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)
#
#     mock_echo.print.assert_called_with("Bad Error")


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_scans_if_installed(
    scan_action: ScanAction,
    mock_secureli_config: MagicMock,
    mock_language_support: MagicMock,
    mock_scanner: MagicMock,
    mock_language_analyzer: MagicMock,
):
    mock_language_analyzer.analyze.return_value = AnalyzeResult(
        language_proportions={"RadLang": 1.0},
        skipped_files=[],
    )
    mock_secureli_config.load.return_value = SecureliConfig(
        languages=["RadLang"], version_installed="abc123"
    )
    mock_language_support.version_for_language.return_value = "abc123"

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

    mock_scanner.scan_repo.assert_called_once()


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_continue_scan_if_upgrade_canceled(
    scan_action: ScanAction,
    mock_secureli_config: MagicMock,
    mock_language_support: MagicMock,
    mock_scanner: MagicMock,
    mock_echo: MagicMock,
    mock_language_analyzer: MagicMock,
):
    mock_language_analyzer.analyze.return_value = AnalyzeResult(
        language_proportions={"RadLang": 1.0},
        skipped_files=[],
    )
    mock_secureli_config.load.return_value = SecureliConfig(
        languages=["RadLang"], version_installed="abc123"
    )
    mock_language_support.version_for_language.return_value = "xyz987"
    mock_echo.confirm.return_value = False

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

    mock_scanner.scan_repo.assert_called_once()


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_does_not_scan_if_not_installed(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_secureli_config: MagicMock,
    mock_echo: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig()
    mock_echo.confirm.return_value = False

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

    mock_scanner.scan_repo.assert_not_called()


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_does_not_add_ignore_if_always_yes_is_true(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_settings_repository: MagicMock,
    mock_default_settings: MagicMock,
    mock_pass_install_verification: MagicMock,
):
    mock_failure = Failure(
        repo="some-repo", id="some-hook-id", file="some-failed-file.py"
    )
    mock_scanner.scan_repo.return_value = ScanResult(
        successful=True, output="some-output", failures=[mock_failure]
    )

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, True)

    mock_settings_repository.save.assert_not_called()


def test_that_scan_checks_for_updates(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_secureli_config: MagicMock,
    mock_pass_install_verification: MagicMock,
):
    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, always_yes=True)
    mock_scanner.pre_commit.check_for_hook_updates.assert_called_once()


def test_that_scan_only_checks_for_updates_periodically(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_get_time_near_epoch: MagicMock,
    mock_secureli_config: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig()

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, always_yes=True)
    mock_scanner.pre_commit.check_for_hook_updates.assert_not_called()


def test_that_scan_update_check_uses_pre_commit_config(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_secureli_config: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig()
    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, always_yes=True)
    mock_scanner.pre_commit.get_pre_commit_config.assert_called_once()


# Test that _check_secureli_hook_updates returns UP_TO_DATE if no hooks need updating
def test_scan_update_check_return_value_when_up_to_date(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_secureli_config: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig()
    result = scan_action._check_secureli_hook_updates(test_folder_path)
    assert result.outcome == VerifyOutcome.UP_TO_DATE


# Test that _check_secureli_hook_updates returns UPDATE_CANCELED if hooks need updating
def test_scan_update_check_return_value_when_not_up_to_date(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_secureli_config: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig()
    mock_scanner.pre_commit.check_for_hook_updates.return_value = {
        "http://example-repo.com/": RevisionPair(oldRev="old-rev", newRev="new-rev")
    }
    result = scan_action._check_secureli_hook_updates(test_folder_path)
    assert result.outcome == VerifyOutcome.UPDATE_CANCELED


# Validate that scan_repo persists changes to the .secureli.yaml file after checking for hook updates
def test_that_scan_update_check_updates_last_check_time(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_get_time_far_from_epoch: MagicMock,
    mock_secureli_config: MagicMock,
    mock_pass_install_verification: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig(
        languages=["RadLang", "BadLang"], version_installed="abc123"
    )
    mock_secureli_config.verify.return_value = VerifyConfigOutcome.UP_TO_DATE
    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, always_yes=True)
    mock_secureli_config.save.assert_called_once()
    assert mock_secureli_config.save.call_args.args[0].last_hook_update_check == 1e6

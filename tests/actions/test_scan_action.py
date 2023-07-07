from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock, patch

import os
import pytest

from secureli.actions.action import ActionDependencies
from secureli.actions.scan import ScanAction
from secureli.repositories.secureli_config import SecureliConfig
from secureli.repositories.settings import (
    SecureliFile,
    PreCommitSettings,
    PreCommitRepo,
    PreCommitHook,
    EchoSettings,
    EchoLevel,
    LanguageSupportSettings,
    RepoFilesSettings,
)
from secureli.services.scanner import ScanMode, ScanResult, Failure, OutputParseErrors

test_folder_path = Path("does-not-matter")


@pytest.fixture()
def mock_scanner() -> MagicMock:
    mock_scanner = MagicMock()
    mock_scanner.scan_repo.return_value = ScanResult(successful=True, failures=[])
    return mock_scanner


@pytest.fixture()
def mock_updater() -> MagicMock:
    mock_updater = MagicMock()
    return mock_updater


@pytest.fixture()
def mock_default_settings(mock_settings_repository: MagicMock) -> MagicMock:
    mock_echo_settings = EchoSettings(EchoLevel.info)
    mock_settings_file = SecureliFile(echo=mock_echo_settings)
    mock_settings_repository.load.return_value = mock_settings_file

    return mock_settings_repository


@pytest.fixture()
def mock_default_settings_populated(mock_settings_repository: MagicMock) -> MagicMock:
    mock_failure = Failure(
        repo="some-repo", id="some-hook-id", file="some-failed-file.py"
    )
    mock_echo_settings = EchoSettings(EchoLevel.info)
    mock_pre_commit_hook_settings = PreCommitHook(id=mock_failure.id)
    mock_pre_commit_repo_settings = PreCommitRepo(
        url=mock_failure.repo, hooks=[mock_pre_commit_hook_settings]
    )
    mock_pre_commit_settings = PreCommitSettings(repos=[mock_pre_commit_repo_settings])
    mock_settings_file = SecureliFile(
        echo=mock_echo_settings, pre_commit=mock_pre_commit_settings
    )
    mock_settings_repository.load.return_value = mock_settings_file

    return mock_settings_repository


@pytest.fixture()
def mock_default_settings_ignore_already_exists(
    mock_settings_repository: MagicMock,
) -> MagicMock:
    mock_failure = Failure(
        repo="some-repo", id="some-hook-id", file="some-failed-file.py"
    )
    mock_echo_settings = EchoSettings(EchoLevel.info)
    mock_pre_commit_hook_settings = PreCommitHook(
        id=mock_failure.id, exclude_file_patterns=[mock_failure.file]
    )
    mock_pre_commit_repo_settings = PreCommitRepo(
        url=mock_failure.repo,
        hooks=[mock_pre_commit_hook_settings],
        suppressed_hook_ids=[mock_failure.id],
    )
    mock_pre_commit_settings = PreCommitSettings(repos=[mock_pre_commit_repo_settings])
    mock_settings_file = SecureliFile(
        echo=mock_echo_settings, pre_commit=mock_pre_commit_settings
    )
    mock_settings_repository.load.return_value = mock_settings_file

    return mock_settings_repository


@pytest.fixture()
def mock_pass_install_verification(
    mock_secureli_config: MagicMock, mock_language_support: MagicMock
):
    mock_secureli_config.load.return_value = SecureliConfig(
        overall_language="RadLang", version_installed="abc123"
    )
    mock_language_support.version_for_language.return_value = "abc123"


@pytest.fixture()
def action_deps(
    mock_echo: MagicMock,
    mock_language_analyzer: MagicMock,
    mock_language_support: MagicMock,
    mock_scanner: MagicMock,
    mock_secureli_config: MagicMock,
    mock_updater: MagicMock,
) -> ActionDependencies:
    return ActionDependencies(
        mock_echo,
        mock_language_analyzer,
        mock_language_support,
        mock_scanner,
        mock_secureli_config,
        mock_updater,
    )


@pytest.fixture()
def scan_action(
    action_deps: ActionDependencies,
    mock_logging_service: MagicMock,
    mock_settings_repository: MagicMock,
) -> ScanAction:
    return ScanAction(
        action_deps=action_deps,
        echo=action_deps.echo,
        logging=mock_logging_service,
        scanner=action_deps.scanner,
        settings_repository=mock_settings_repository,
    )


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_errors_if_not_successful(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_echo: MagicMock,
):
    mock_scanner.scan_repo.return_value = ScanResult(
        successful=False, output="Bad Error", failures=[]
    )

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

    mock_echo.print.assert_called_with("Bad Error")


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_scans_if_installed(
    scan_action: ScanAction,
    mock_secureli_config: MagicMock,
    mock_language_support: MagicMock,
    mock_scanner: MagicMock,
    mock_echo: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig(
        overall_language="RadLang", version_installed="abc123"
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
):
    mock_secureli_config.load.return_value = SecureliConfig(
        overall_language="RadLang", version_installed="abc123"
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
def test_that_scan_repo_handles_declining_to_add_ignore_for_failures(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_echo: MagicMock,
    mock_settings_repository: MagicMock,
    mock_default_settings: MagicMock,
    mock_pass_install_verification: MagicMock,
):
    mock_failures = [
        Failure(repo="some-repo", id="some-hook-id", file="some-failed-file.py")
    ]
    mock_scanner.scan_repo.return_value = ScanResult(
        successful=True, output="some-output", failures=mock_failures
    )
    mock_echo.confirm.return_value = False

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

    mock_settings_repository.load.assert_called_once()
    mock_settings_repository.save.assert_not_called()


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_adds_ignore_for_all_files_when_prompted(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_echo: MagicMock,
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
    mock_echo.confirm.side_effect = [True, True, True]

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

    saved_settings = mock_settings_repository.save.call_args.kwargs["settings"]
    saved_suppressed_id = saved_settings.pre_commit.repos[0].suppressed_hook_ids[0]
    expected_suppressed_id = mock_failure.id

    assert saved_suppressed_id is expected_suppressed_id


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_adds_ignore_for_all_files_when_settings_exist_when_prompted(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_echo: MagicMock,
    mock_settings_repository: MagicMock,
    mock_default_settings_populated: MagicMock,
    mock_pass_install_verification: MagicMock,
):
    mock_failure = Failure(
        repo="some-repo", id="some-hook-id", file="some-failed-file.py"
    )
    mock_scanner.scan_repo.return_value = ScanResult(
        successful=True, output="some-output", failures=[mock_failure]
    )
    mock_echo.confirm.side_effect = [True, True, True]

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

    saved_settings = mock_settings_repository.save.call_args.kwargs["settings"]
    saved_suppressed_id = saved_settings.pre_commit.repos[0].suppressed_hook_ids[0]
    expected_suppressed_id = mock_failure.id

    assert saved_suppressed_id is expected_suppressed_id


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_skips_ignore_for_all_files_when_ignore_already_exists(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_echo: MagicMock,
    mock_settings_repository: MagicMock,
    mock_default_settings_ignore_already_exists: MagicMock,
    mock_pass_install_verification: MagicMock,
):
    mock_failure = Failure(
        repo="some-repo", id="some-hook-id", file="some-failed-file.py"
    )
    mock_scanner.scan_repo.return_value = ScanResult(
        successful=True, output="some-output", failures=[mock_failure]
    )
    mock_echo.confirm.side_effect = [True, True, True]

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

    saved_settings = mock_settings_repository.save.call_args.kwargs["settings"]
    saved_suppressed_id = saved_settings.pre_commit.repos[0].suppressed_hook_ids[0]
    expected_suppressed_id = mock_failure.id

    assert saved_suppressed_id is expected_suppressed_id


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_adds_ignore_for_one_file_when_prompted(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_echo: MagicMock,
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
    mock_echo.confirm.side_effect = [True, True, False, True]

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

    saved_settings = mock_settings_repository.save.call_args.kwargs["settings"]
    saved_excluded_file = (
        saved_settings.pre_commit.repos[0].hooks[0].exclude_file_patterns[0]
    )
    expected_excluded_file = mock_failure.file

    assert saved_excluded_file is expected_excluded_file


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_adds_ignore_for_one_file_when_settings_exist_when_prompted(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_echo: MagicMock,
    mock_settings_repository: MagicMock,
    mock_default_settings_populated: MagicMock,
    mock_pass_install_verification: MagicMock,
):
    mock_failure = Failure(
        repo="some-repo", id="some-hook-id", file="some-failed-file.py"
    )
    mock_scanner.scan_repo.return_value = ScanResult(
        successful=True, output="some-output", failures=[mock_failure]
    )
    mock_echo.confirm.side_effect = [True, True, False, True]

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

    saved_settings = mock_settings_repository.save.call_args.kwargs["settings"]
    saved_excluded_file = (
        saved_settings.pre_commit.repos[0].hooks[0].exclude_file_patterns[0]
    )
    expected_excluded_file = mock_failure.file

    assert saved_excluded_file is expected_excluded_file


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_skips_ignore_for_one_file_when_ignore_already_present(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_echo: MagicMock,
    mock_settings_repository: MagicMock,
    mock_default_settings_ignore_already_exists: MagicMock,
    mock_pass_install_verification: MagicMock,
):
    mock_failure = Failure(
        repo="some-repo", id="some-hook-id", file="some-failed-file.py"
    )
    mock_scanner.scan_repo.return_value = ScanResult(
        successful=True, output="some-output", failures=[mock_failure]
    )
    mock_echo.confirm.side_effect = [True, True, False, True]

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

    saved_settings = mock_settings_repository.save.call_args.kwargs["settings"]
    saved_excluded_file = (
        saved_settings.pre_commit.repos[0].hooks[0].exclude_file_patterns[0]
    )
    expected_excluded_file = mock_failure.file

    assert saved_excluded_file is expected_excluded_file


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_handles_missing_repo_while_adding_ignore_rule(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_echo: MagicMock,
    mock_settings_repository: MagicMock,
    mock_default_settings_populated: MagicMock,
    mock_pass_install_verification: MagicMock,
):
    mock_failure = Failure(
        repo=OutputParseErrors.REPO_NOT_FOUND,
        id="some-hook-id",
        file="some-failed-file.py",
    )
    mock_scanner.scan_repo.return_value = ScanResult(
        successful=True, output="some-output", failures=[mock_failure]
    )
    mock_echo.confirm.side_effect = [True, True]

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

    mock_echo.print.assert_any_call(
        "Unable to add an ignore for some-hook-id, SeCureLI was unable to identify the repo it belongs to."
    )


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_does_not_add_ignore_if_both_ignore_types_declined(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_echo: MagicMock,
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
    mock_echo.confirm.side_effect = [True, True, False, False]

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

    saved_settings = mock_settings_repository.save.call_args.kwargs["settings"]

    assert saved_settings is mock_settings_repository.load.return_value


@mock.patch.dict(os.environ, {"API_KEY": "", "API_ENDPOINT": ""}, clear=True)
def test_that_scan_repo_does_not_add_ignore_if_all_failures_declined(
    scan_action: ScanAction,
    mock_scanner: MagicMock,
    mock_echo: MagicMock,
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
    mock_echo.confirm.side_effect = [True, False]

    scan_action.scan_repo(test_folder_path, ScanMode.STAGED_ONLY, False)

    saved_settings = mock_settings_repository.save.call_args.kwargs["settings"]

    assert saved_settings is mock_settings_repository.load.return_value


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

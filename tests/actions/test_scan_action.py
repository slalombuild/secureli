import os
from pathlib import Path
from unittest import mock
from unittest.mock import MagicMock

import pytest

from secureli.actions.action import ActionDependencies
from secureli.actions.scan import ScanAction
from secureli.repositories.secureli_config import SecureliConfig
from secureli.repositories.settings import (
    SecureliFile,
    EchoSettings,
    EchoLevel,
)
from secureli.services.scanner import ScanMode, ScanResult, Failure

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
    mock_echo_settings = EchoSettings(EchoLevel.info)
    mock_settings_file = SecureliFile(
        echo=mock_echo_settings,
    )
    mock_settings_repository.load.return_value = mock_settings_file

    return mock_settings_repository


@pytest.fixture()
def mock_default_settings_ignore_already_exists(
    mock_settings_repository: MagicMock,
) -> MagicMock:
    mock_echo_settings = EchoSettings(EchoLevel.info)
    mock_settings_file = SecureliFile(
        echo=mock_echo_settings,
    )
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
):
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

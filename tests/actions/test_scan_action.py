from pathlib import Path
from unittest.mock import MagicMock

import pytest

from secureli.actions.action import ActionDependencies
from secureli.actions.scan import ScanAction
from secureli.repositories.secureli_config import SecureliConfig
from secureli.services.scanner import ScanMode, ScanResult

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
def action_deps(
    mock_echo: MagicMock,
    mock_language_analyzer: MagicMock,
    mock_language_support: MagicMock,
    mock_scanner: MagicMock,
    mock_secureli_config: MagicMock,
    mock_updater: MagicMock,
    mock_pre_commit: MagicMock,
) -> ActionDependencies:
    return ActionDependencies(
        mock_echo,
        mock_language_analyzer,
        mock_language_support,
        mock_scanner,
        mock_secureli_config,
        mock_updater,
        mock_pre_commit,
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

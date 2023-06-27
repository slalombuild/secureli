from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from secureli.abstractions.pre_commit import HookConfiguration
from secureli.repositories.secureli_config import SecureliConfig
from secureli.services.logging import LoggingService, LogAction

test_folder_path = Path(".")


@pytest.fixture()
def mock_path(mocker: MockerFixture) -> MagicMock:
    mock_file_path = MagicMock()
    mock_file_path.return_value = Path(".secureli/logs/fancy-branch")

    mock_path_instance = MagicMock()
    mock_path_instance.__truediv__.return_value = mock_file_path

    mock_path_class = mocker.patch("secureli.services.logging.Path")
    mock_path_class.return_value = mock_path_instance

    return mock_file_path


@pytest.fixture()
def mock_open(mocker: MockerFixture) -> MagicMock:
    mock_open = mocker.mock_open()

    mocker.patch("builtins.open", mock_open)

    return mock_open


@pytest.fixture()
def mock_open(mocker: MockerFixture) -> MagicMock:
    mock_open = mocker.mock_open()

    mocker.patch("builtins.open", mock_open)

    return mock_open


@pytest.fixture()
def logging_service(
    mock_pre_commit: MagicMock, mock_secureli_config: MagicMock
) -> LoggingService:
    return LoggingService(
        pre_commit=mock_pre_commit,
        secureli_config=mock_secureli_config,
    )


def test_that_logging_service_success_creates_logs_folder_if_not_exists(
    logging_service: LoggingService,
    mock_path: MagicMock,
    mock_open: MagicMock,
    mock_secureli_config: MagicMock,
    mock_pre_commit: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig(
        overall_language="RadLang", version_installed="abc123"
    )
    mock_pre_commit.get_configuration.return_value = HookConfiguration(repos=[])
    logging_service.success(test_folder_path, LogAction.init)

    mock_path.parent.mkdir.assert_called_once()


def test_that_logging_service_failure_creates_logs_folder_if_not_exists(
    logging_service: LoggingService,
    mock_path: MagicMock,
    mock_open: MagicMock,
    mock_secureli_config: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig(
        overall_language=None, version_installed=None
    )

    logging_service.failure(
        test_folder_path, LogAction.init, "Horrible Failure", None, None
    )

    mock_path.parent.mkdir.assert_called_once()


def test_that_logging_service_success_logs_none_for_hook_config_if_not_initialized(
    logging_service: LoggingService,
    mock_path: MagicMock,
    mock_open: MagicMock,
    mock_secureli_config: MagicMock,
):
    # Uninitialized configuration
    mock_secureli_config.load.return_value = SecureliConfig(
        overall_language=None, version_installed=None
    )

    log_entry = logging_service.success(test_folder_path, LogAction.build)

    assert log_entry.hook_config is None

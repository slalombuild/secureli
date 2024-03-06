from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from secureli.repositories import settings


@pytest.fixture()
def non_existent_path(mocker: MockerFixture) -> MagicMock:
    config_file_path = MagicMock()
    config_file_path.exists.return_value = False
    config_file_path.is_dir.return_value = False
    mock_folder_path = MagicMock()
    mock_folder_path.__truediv__.return_value = config_file_path

    mock_path_class = MagicMock()
    mock_path_class.return_value = mock_folder_path

    mocker.patch("secureli.repositories.settings.Path", mock_path_class)

    return mock_folder_path


@pytest.fixture()
def existent_path(mocker: MockerFixture) -> MagicMock:
    config_file_path = MagicMock()
    config_file_path.exists.return_value = True
    config_file_path.is_dir.return_value = False
    mock_folder_path = MagicMock()
    mock_folder_path.__truediv__.return_value = config_file_path

    mock_path_class = MagicMock()
    mock_path_class.return_value = mock_folder_path

    mock_open = mocker.mock_open(
        read_data="""
        echo:
          level: ERROR
        repo_files:
          exclude_file_patterns:
          - .idea/
          ignored_file_extensions:
          - .pyc
          - .drawio
          - .png
          - .jpg
          max_file_size: 1000000
    """
    )
    mocker.patch("builtins.open", mock_open)

    mocker.patch("secureli.repositories.settings.Path", mock_path_class)

    return mock_folder_path


@pytest.fixture()
def settings_repository() -> settings.SecureliRepository:
    settings_repository = settings.SecureliRepository()
    return settings_repository


def test_that_settings_file_loads_settings_when_present(
    existent_path: MagicMock,
    settings_repository: settings.SecureliRepository,
):
    secureli_file = settings_repository.load(existent_path)

    assert secureli_file.echo.level == settings.EchoLevel.error


def test_that_settings_file_created_when_not_present(
    non_existent_path: MagicMock,
    settings_repository: settings.SecureliRepository,
):
    secureli_file = settings_repository.load(non_existent_path)

    assert secureli_file is not None


def test_that_repo_saves_config(
    existent_path: MagicMock,
    mock_open: MagicMock,
    settings_repository: settings.SecureliRepository,
):
    echo_level = settings.EchoSettings(level=settings.EchoLevel.info)
    settings_file = settings.SecureliFile(echo=echo_level)
    settings_repository.save(settings_file)

    mock_open.assert_called_once()


def test_that_repo_saves_without_echo_level(
    existent_path: MagicMock,
    mock_open: MagicMock,
    settings_repository: settings.SecureliRepository,
):
    settings_file = settings.SecureliFile()
    settings_repository.save(settings_file)

    mock_open.assert_called_once()

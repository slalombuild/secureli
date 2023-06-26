from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from secureli.repositories.secureli_config import (
    SecureliConfigRepository,
    SecureliConfig,
)

test_folder_path = Path(".")


@pytest.fixture()
def non_existent_path(mocker: MockerFixture) -> MagicMock:
    config_file_path = MagicMock()
    config_file_path.exists.return_value = False
    config_file_path.is_dir.return_value = False
    mock_folder_path = MagicMock()
    mock_folder_path.__truediv__.return_value = config_file_path

    mock_secureli_folder_path = MagicMock()
    mock_secureli_folder_path.__truediv__.return_value = mock_folder_path

    mock_path_class = MagicMock()
    mock_path_class.return_value = mock_secureli_folder_path

    mocker.patch("secureli.repositories.secureli_config.Path", mock_path_class)

    return mock_folder_path


@pytest.fixture()
def existent_path(mocker: MockerFixture) -> MagicMock:
    config_file_path = MagicMock()
    config_file_path.exists.return_value = True
    config_file_path.is_dir.return_value = False
    mock_folder_path = MagicMock()
    mock_folder_path.__truediv__.return_value = config_file_path

    mock_secureli_folder_path = MagicMock()
    mock_secureli_folder_path.__truediv__.return_value = mock_folder_path

    mock_path_class = MagicMock()
    mock_path_class.return_value = mock_secureli_folder_path

    mock_open = mocker.mock_open(
        read_data="""
        overall_language: RadLang
        version_installed: mock-version-id
    """
    )
    mocker.patch("builtins.open", mock_open)

    mocker.patch("secureli.repositories.secureli_config.Path", mock_path_class)

    return mock_folder_path


@pytest.fixture()
def secureli_config() -> SecureliConfigRepository:
    secureli_config = SecureliConfigRepository()
    return secureli_config


def test_that_repo_synthesizes_default_config_when_missing(
    non_existent_path: MagicMock,
    secureli_config: SecureliConfigRepository,
):
    config = secureli_config.load(test_folder_path)

    assert config.overall_language is None


def test_that_repo_loads_config_when_present(
    existent_path: MagicMock,
    secureli_config: SecureliConfigRepository,
):
    config = secureli_config.load(test_folder_path)

    assert config.overall_language == "RadLang"


def test_that_repo_saves_config(
    existent_path: MagicMock,
    mock_open: MagicMock,
    secureli_config: SecureliConfigRepository,
):
    config = SecureliConfig(overall_language="AwesomeLang")
    secureli_config.save(test_folder_path, config)

    mock_open.assert_called_once()

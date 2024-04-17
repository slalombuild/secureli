from pathlib import Path
from unittest.mock import MagicMock
import pytest
from pytest_mock import MockerFixture

import secureli.modules.shared.models.repository as RepositoryModels
from secureli.repositories import secureli_config


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
        languages:
        - RadLang
        version_installed: mock-version-id
    """
    )
    mocker.patch("builtins.open", mock_open)

    mocker.patch("secureli.repositories.secureli_config.Path", mock_path_class)

    return mock_folder_path


@pytest.fixture()
def existent_path_old_schema(mocker: MockerFixture) -> MagicMock:
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
def secureli_config_fixture() -> secureli_config.SecureliConfigRepository:
    secureli_config_fixture = secureli_config.SecureliConfigRepository()
    return secureli_config_fixture


def test_that_repo_synthesizes_default_config_when_missing(
    non_existent_path: MagicMock,
    secureli_config_fixture: secureli_config.SecureliConfigRepository,
):
    config = secureli_config_fixture.load()

    assert config.languages is None


def test_that_repo_loads_config_when_present(
    existent_path: MagicMock,
    secureli_config_fixture: secureli_config.SecureliConfigRepository,
):
    config = secureli_config_fixture.load()

    assert config.languages == ["RadLang"]


def test_that_repo_saves_config(
    existent_path: MagicMock,
    mock_open: MagicMock,
    secureli_config_fixture: secureli_config.SecureliConfigRepository,
):
    config = RepositoryModels.SecureliConfig(languages=["AwesomeLang"])
    secureli_config_fixture.save(config)

    mock_open.assert_called_once()


def test_that_repo_validates_most_current_schema(
    existent_path: MagicMock,
    secureli_config_fixture: secureli_config.SecureliConfigRepository,
):
    result = secureli_config_fixture.verify()

    assert result == RepositoryModels.VerifyConfigOutcome.UP_TO_DATE


def test_that_repo_catches_deprecated_schema(
    existent_path_old_schema: MagicMock,
    secureli_config_fixture: secureli_config.SecureliConfigRepository,
):
    result = secureli_config_fixture.verify()

    assert result == RepositoryModels.VerifyConfigOutcome.OUT_OF_DATE


def test_that_repo_does_not_validate_with_missing_config(
    non_existent_path: MagicMock,
    secureli_config_fixture: secureli_config.SecureliConfigRepository,
):
    result = secureli_config_fixture.verify()

    assert result == RepositoryModels.VerifyConfigOutcome.MISSING


def test_that_repo_updates_config(
    existent_path_old_schema: MagicMock,
    secureli_config_fixture: secureli_config.SecureliConfigRepository,
):
    result = secureli_config_fixture.update()

    assert result.languages


def test_that_update_returns_empty_config_if_missing_config_file(
    non_existent_path: MagicMock,
    secureli_config_fixture: secureli_config.SecureliConfigRepository,
):
    result = secureli_config_fixture.update()

    assert result == RepositoryModels.SecureliConfig()

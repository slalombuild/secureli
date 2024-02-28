from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture


@pytest.fixture()
def mock_open_repo_config(mocker: MockerFixture) -> MagicMock:
    mock_open_repo_config = mocker.mock_open(
        read_data="languages: -RadLang\nversion_installed: 5"
    )
    mocker.patch("builtins.open", mock_open_repo_config)
    return mock_open_repo_config


@pytest.fixture()
def mock_secureli_meta_path(mocker: MockerFixture) -> MagicMock:
    mock_path_instance = MagicMock()

    mock_path_class = mocker.patch(
        "secureli.modules.shared.utilities.secureli_meta.Path"
    )
    mock_path_class.return_value = mock_path_instance

    return mock_path_instance

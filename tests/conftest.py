from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from secureli.modules.shared.abstractions.pre_commit import ExecuteResult


# Register generic mocks you'd like available for every test.


@pytest.fixture()
def mock_pre_commit() -> MagicMock:
    mock_pre_commit = MagicMock()
    mock_pre_commit.execute_hooks.return_value = ExecuteResult(
        successful=True, output=""
    )
    return mock_pre_commit


@pytest.fixture()
def mock_secureli_config() -> MagicMock:
    mock_secureli_config = MagicMock()
    return mock_secureli_config


@pytest.fixture()
def mock_settings_repository() -> MagicMock:
    mock_settings_repository = MagicMock()
    return mock_settings_repository


@pytest.fixture()
def mock_open(mocker: MockerFixture) -> MagicMock:
    mock_open = mocker.mock_open()
    mocker.patch("builtins.open", mock_open)
    return mock_open

from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

import secureli.container
import secureli.main


@pytest.fixture()
def mock_container(mocker: MockerFixture) -> MagicMock:
    mock_container_instance = MagicMock()
    mocker.patch("secureli.main.container", mock_container_instance)
    return mock_container_instance


def test_that_setup_wires_up_container(mock_container: MagicMock):
    secureli.main.setup()
    mock_container.init_resources.assert_called_once()
    mock_container.wire.assert_called_once()


def test_that_init_creates_initializer_action_and_executes(mock_container: MagicMock):
    secureli.main.init()

    mock_container.initializer_action.assert_called_once()


def test_that_build_creates_build_action_and_executes(mock_container: MagicMock):
    secureli.main.build()

    mock_container.build_action.assert_called_once()


def test_that_scan_is_tbd(mock_container: MagicMock):
    secureli.main.scan()

    mock_container.scan_action.assert_called_once()


def test_that_update_is_tbd(mock_container: MagicMock):
    secureli.main.update()

    mock_container.update_action.assert_called_once()

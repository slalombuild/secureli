from unittest.mock import MagicMock
from typer.testing import CliRunner

import pytest
from pytest_mock import MockerFixture

import secureli.container
import secureli.main
from secureli.utilities.secureli_meta import secureli_version


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


@pytest.mark.parametrize("test_input", ["-v", "--version"])
def test_that_app_implements_version_option(
    test_input: str, request: pytest.FixtureRequest
):
    result = CliRunner().invoke(secureli.main.app, [test_input])
    mock_container = request.getfixturevalue("mock_container")

    assert result.exit_code is 0
    assert secureli_version() in result.stdout
    mock_container.init_resources.assert_not_called()
    mock_container.wire.assert_not_called()


def test_that_app_ignores_version_callback(mock_container: MagicMock):
    result = CliRunner().invoke(secureli.main.app, ["scan"])

    assert result.exit_code is 0
    assert secureli_version() not in result.stdout
    mock_container.init_resources.assert_called_once()
    mock_container.wire.assert_called_once()

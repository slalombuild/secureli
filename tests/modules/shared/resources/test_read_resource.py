from typing import Callable
from unittest.mock import MagicMock, mock_open

import pytest
from pytest_mock import MockerFixture

import secureli.modules.shared.resources


@pytest.fixture()
def mock_open_resource(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("builtins.open", mock_open(read_data="sample_data"))


@pytest.fixture()
def read_resource(mock_open_resource: MagicMock) -> Callable[[str], str]:
    return secureli.modules.shared.resources.read_resource


def test_that_read_resource_opens_specified_file_in_files_folder(
    read_resource: Callable[[str], str], mock_open_resource: MagicMock
):
    result = read_resource("build.txt")

    assert result == "sample_data"


def test_that_read_resource_raises_exception_when_file_not_found(
    read_resource: Callable[[str], str], mock_open_resource: MagicMock
):
    with pytest.raises(ValueError):
        read_resource("invalid.txt")

from subprocess import CompletedProcess
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from secureli.modules.shared.utilities.git_meta import (
    git_user_email,
    origin_url,
    current_branch_name,
)

mock_git_origin_url = (
    r"git@github.com:my-org/repo%20with%20spaces.git"  # disable-pii-scan
)


@pytest.fixture()
def mock_subprocess(mocker: MockerFixture) -> MagicMock:
    mock_subprocess = mocker.patch(
        "secureli.modules.shared.utilities.git_meta.subprocess"
    )
    mock_subprocess.run.return_value = CompletedProcess(
        args=[],
        returncode=0,
        stdout="great.engineer@slalom.com\n".encode("utf8"),  # disable-pii-scan
    )
    return mock_subprocess


@pytest.fixture()
def mock_configparser(mocker: MockerFixture) -> MagicMock:
    mock_configparser = mocker.patch(
        "secureli.modules.shared.utilities.git_meta.configparser"
    )
    mock_configparser_instance = MagicMock()
    mock_configparser_instance['remote "origin"'].get.return_value = (
        "https://fake-build.com/git/repo"
    )
    mock_configparser.ConfigParser.return_value = mock_configparser_instance
    return mock_configparser_instance


@pytest.fixture()
def mock_open_git_head(mocker: MockerFixture) -> MagicMock:
    mock_open_git_head = mocker.mock_open(
        read_data="#fakeline\nref: refs/heads/feature/wicked-sick-branch"
    )
    mocker.patch("builtins.open", mock_open_git_head)
    return mock_open_git_head


@pytest.fixture()
def mock_open_git_origin(mocker: MockerFixture) -> MagicMock:
    mock_open_git_config = mocker.mock_open(
        read_data='[remote "origin"]'
        f"\n    url = {mock_git_origin_url}"
        "\n    fetch = +refs/heads/*:refs/remotes/origin/*"
    )
    mocker.patch("builtins.open", mock_open_git_config)
    return mock_open_git_config


@pytest.fixture()
def mock_open_io_error(mocker: MockerFixture) -> MagicMock:
    mock_open_io_error = mocker.patch("builtins.open")
    mock_open_io_error.side_effect = IOError
    return mock_open_io_error


def test_git_user_email_loads_user_email_via_git_subprocess(mock_subprocess: MagicMock):
    result = git_user_email()

    mock_subprocess.run.assert_called_once()
    assert (
        result == "great.engineer@slalom.com"  # disable-pii-scan
    )  # note: without trailing newline


def test_origin_url_parses_config_to_get_origin_url(mock_configparser: MagicMock):
    result = origin_url()

    mock_configparser.read.assert_called_once_with(".git/config")
    assert result == "https://fake-build.com/git/repo"


def test_current_branch_name_finds_ref_name_from_head_file(
    mock_open_git_head: MagicMock,
):
    result = current_branch_name()

    assert result == "feature/wicked-sick-branch"


def test_current_branch_name_yields_unknown_due_to_io_error(
    mock_open_io_error: MagicMock,
):
    result = current_branch_name()

    assert result == "UNKNOWN"


def test_configparser_can_read_origin_url_with_percent(mock_open_git_origin: MagicMock):
    assert origin_url() == mock_git_origin_url

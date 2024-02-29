from pathlib import Path
from unittest.mock import MagicMock
import unittest.mock as um

import pytest
from pytest_mock import MockerFixture

from secureli.modules.language_analyzer.language_analyzer_services.git_ignore import (
    GitIgnoreService,
    BadIgnoreBlockError,
)


@pytest.fixture()
def mock_open_with_gitignore(mocker: MockerFixture) -> MagicMock:
    mock_open = mocker.mock_open(read_data="# existing contents\n")
    mocker.patch("builtins.open", mock_open)
    return mock_open


@pytest.fixture()
def mock_open_with_ignored_patterns(mocker: MockerFixture) -> MagicMock:
    mock_open = mocker.mock_open(read_data="*.py\n*.txt\n#comment!")
    mocker.patch("builtins.open", mock_open)
    return mock_open


@pytest.fixture()
def mock_open_with_gitignore_existing_secureli_config(
    mocker: MockerFixture,
) -> MagicMock:
    header = "# Secureli-generated files (do not modify):"
    footer = "# End Secureli-generated files"
    mock_open = mocker.mock_open(read_data=f"# existing contents\n{header}...{footer}")
    mocker.patch("builtins.open", mock_open)
    return mock_open


@pytest.fixture()
def mock_open_with_gitignore_broken_secureli_config(mocker: MockerFixture) -> MagicMock:
    header = "# Secureli-generated files (do not modify):"
    footer = "# INVALID FOOTER"
    mock_open = mocker.mock_open(read_data=f"# existing contents\n{header}...{footer}")
    mocker.patch("builtins.open", mock_open)
    return mock_open


@pytest.fixture()
def mock_path(mocker: MockerFixture) -> MagicMock:
    mock_path_class = mocker.patch(
        "secureli.modules.language_analyzer.language_analyzer_services.git_ignore.Path"
    )
    mock_path_instance = MagicMock()
    mock_path_class.return_value = mock_path_instance
    return mock_path_instance


@pytest.fixture
def git_ignore(mock_path: MagicMock) -> GitIgnoreService:
    git_ignore = GitIgnoreService()
    git_ignore.git_ignore_path = mock_path
    return git_ignore


def test_that_git_ignore_creates_file_if_missing(
    git_ignore: GitIgnoreService, mock_path: MagicMock, mock_open: MagicMock
):
    mock_path.exists.return_value = False

    with um.patch.object(Path, "exists") as mock_exists:
        mock_exists.return_value = False

        git_ignore.ignore_secureli_files()

        mock_open.return_value.write.assert_called_once()

        args, _ = mock_open.return_value.write.call_args_list[0]
        assert args[0].find("# existing contents") == -1
        assert args[0].find(".secureli") != -1
        assert args[0].find(git_ignore.header) != -1
        assert args[0].find(git_ignore.footer) != -1


def test_that_git_ignore_appends_to_existing_file_if_block_is_missing(
    git_ignore: GitIgnoreService,
    mock_path: MagicMock,
    mock_open_with_gitignore: MagicMock,
):
    mock_path.exists.return_value = True

    git_ignore.ignore_secureli_files()

    mock_open_with_gitignore.return_value.write.assert_called_once()

    args, _ = mock_open_with_gitignore.return_value.write.call_args_list[0]
    assert args[0].find("# existing contents") == 0
    assert args[0].find(".secureli") != -1


def test_that_git_ignore_updates_existing_file_if_block_is_present(
    git_ignore: GitIgnoreService,
    mock_path: MagicMock,
    mock_open_with_gitignore_existing_secureli_config: MagicMock,
):
    mock_path.exists.return_value = True

    git_ignore.ignore_secureli_files()

    mock_open_with_gitignore_existing_secureli_config.return_value.write.assert_called_once()

    (
        args,
        _,
    ) = mock_open_with_gitignore_existing_secureli_config.return_value.write.call_args_list[
        0
    ]
    assert args[0].find("# existing contents") == 0  # still starts with header
    assert args[0].find(".secureli") != -1  # .secureli folder now added
    assert args[0].find("...") == -1  # initial data now missing


def test_that_git_ignore_is_mad_if_header_is_found_without_footer(
    git_ignore: GitIgnoreService,
    mock_path: MagicMock,
    mock_open_with_gitignore_broken_secureli_config: MagicMock,
):
    mock_path.exists.return_value = True

    with pytest.raises(BadIgnoreBlockError):
        git_ignore.ignore_secureli_files()


def test_that_ignore_ignore_finds_and_reads_file(
    git_ignore: GitIgnoreService,
    mock_path: MagicMock,
    mock_open_with_ignored_patterns: MagicMock,
):
    mock_path.exists.return_value = True

    ignored_patterns = git_ignore.ignored_file_patterns()

    assert ignored_patterns == [
        "^(?:.+/)?[^/]*\\.py(?:(?P<ps_d>/).*)?$",
        "^(?:.+/)?[^/]*\\.txt(?:(?P<ps_d>/).*)?$",
    ]


def test_that_ignore_ignore_does_not_find_file_and_returns_empty(
    git_ignore: GitIgnoreService,
    mock_path: MagicMock,
    mock_open_with_ignored_patterns: MagicMock,
):
    mock_path.exists.return_value = False

    ignored_patterns = git_ignore.ignored_file_patterns()

    assert ignored_patterns == []

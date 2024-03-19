from pathlib import Path
from unittest.mock import MagicMock
import pytest
from pytest_mock import MockerFixture

from secureli.modules.shared.abstractions.repo import GitRepo


@pytest.fixture()
def git_repo() -> GitRepo:
    return GitRepo()


@pytest.fixture()
def mock_repo(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("git.Repo", MagicMock())


def test_that_get_commit_diff_returns_file_diff(
    git_repo: GitRepo, mock_repo: MagicMock
):
    mock_files = [Path("test_file.py"), Path("test_file2.py")]
    mock_repo.return_value.head.commit.diff.return_value = mock_files
    result = git_repo.get_commit_diff()
    assert result is mock_files


def test_that_get_commit_diff_returns_empty_list_on_error(
    git_repo: GitRepo, mock_repo: MagicMock
):
    mock_repo.return_value.head = None
    result = git_repo.get_commit_diff()
    assert result == []

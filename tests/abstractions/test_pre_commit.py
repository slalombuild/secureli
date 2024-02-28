import datetime
import shutil
import unittest.mock as um
from pathlib import Path, PosixPath
from subprocess import CompletedProcess
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from secureli.abstractions.pre_commit import (
    InstallResult,
    PreCommitAbstraction,
)
from secureli.repositories.settings import (
    PreCommitSettings,
    PreCommitRepo,
    PreCommitHook,
)

test_folder_path = Path("does-not-matter")
example_git_sha = "a" * 40


@pytest.fixture()
def settings_dict() -> dict:
    return PreCommitSettings(
        repos=[
            PreCommitRepo(
                repo="http://example-repo.com/",
                rev="master",
                hooks=[
                    PreCommitHook(
                        id="hook-id",
                        arguments=None,
                        additional_args=None,
                    )
                ],
            )
        ]
    ).dict()


@pytest.fixture()
def mock_hashlib(mocker: MockerFixture) -> MagicMock:
    mock_hashlib = MagicMock()
    mock_md5 = MagicMock()
    mock_hashlib.md5.return_value = mock_md5
    mock_md5.hexdigest.return_value = "mock-hash-code"
    mocker.patch("secureli.utilities.hash.hashlib", mock_hashlib)
    return mock_hashlib


@pytest.fixture()
def mock_hashlib_no_match(mocker: MockerFixture) -> MagicMock:
    mock_hashlib = MagicMock()
    mock_md5 = MagicMock()
    mock_hashlib.md5.return_value = mock_md5
    mock_md5.hexdigest.side_effect = ["first-hash-code", "second-hash-code"]
    mocker.patch("secureli.utilities.hash.hashlib", mock_hashlib)
    return mock_hashlib


@pytest.fixture()
def mock_data_loader() -> MagicMock:
    mock_data_loader = MagicMock()
    mock_data_loader.return_value = "a: 1"
    return mock_data_loader


@pytest.fixture()
def mock_subprocess(mocker: MockerFixture) -> MagicMock:
    mock_subprocess = MagicMock()
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    mocker.patch("secureli.abstractions.pre_commit.subprocess", mock_subprocess)
    return mock_subprocess


# TODO consider removing if I don't actually need to test anything?
@pytest.fixture()
def mock_echo(mocker: MockerFixture) -> MagicMock:
    mock_echo = MagicMock()
    return mock_echo


@pytest.fixture()
def pre_commit(
    mock_hashlib: MagicMock,
    mock_open: MagicMock,
    mock_subprocess: MagicMock,
) -> PreCommitAbstraction:
    return PreCommitAbstraction(command_timeout_seconds=300, echo=mock_echo)


def test_that_pre_commit_executes_hooks_successfully(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
        execute_result = pre_commit.execute_hooks(test_folder_path)

        assert execute_result.successful
        assert "--all-files" not in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_executes_hooks_successfully_including_all_files(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
        execute_result = pre_commit.execute_hooks(test_folder_path, all_files=True)

        assert execute_result.successful
        assert "--all-files" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_executes_hooks_and_reports_failures(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
        execute_result = pre_commit.execute_hooks(test_folder_path)

        assert not execute_result.successful


def test_that_pre_commit_executes_a_single_hook_if_specified(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
        pre_commit.execute_hooks(test_folder_path, hook_id="detect-secrets")

        assert mock_subprocess.run.call_args_list[0].args[0][-1] == "detect-secrets"


def test_that_pre_commit_executes_hooks_on_specified_files(
    pre_commit: PreCommitAbstraction, mock_subprocess: MagicMock
):
    with (um.patch.object(Path, "exists") as mock_exists,):
        files = ["test_file.py", "test-file.js"]
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)
        pre_commit.execute_hooks(
            test_folder_path,
            hook_id="detect-secrets",
            files=files,
        )

        sub_process_args: [str] = mock_subprocess.run.call_args_list[0].args[0]
        files_arg_idx = sub_process_args.index("--files")

        assert " ".join(files) == sub_process_args[files_arg_idx + 1]


def test_that_pre_commit_does_not_execute_hooks_on_specified_files_if_not_included(
    pre_commit: PreCommitAbstraction, mock_subprocess: MagicMock
):
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_subprocess.return_value = CompletedProcess(args=[], returncode=0)
        pre_commit.execute_hooks(
            test_folder_path,
            hook_id="detect-secrets",
        )
        sub_process_args: [str] = mock_subprocess.run.call_args_list[0].args[0]
        assert "--files" not in sub_process_args


##### autoupdate_hooks #####
def test_that_pre_commit_autoupdate_hooks_executes_successfully(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
        execute_result = pre_commit.autoupdate_hooks(test_folder_path)

        assert execute_result.successful


def test_that_pre_commit_autoupdate_hooks_properly_handles_failed_executions(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
        execute_result = pre_commit.autoupdate_hooks(test_folder_path)

        assert not execute_result.successful


def test_that_pre_commit_autoupdate_hooks_executes_successfully_with_bleeding_edge(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
        execute_result = pre_commit.autoupdate_hooks(
            test_folder_path, bleeding_edge=True
        )

        assert execute_result.successful
        assert "--bleeding-edge" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_autoupdate_hooks_executes_successfully_with_freeze(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
        execute_result = pre_commit.autoupdate_hooks(test_folder_path, freeze=True)

        assert execute_result.successful
        assert "--freeze" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_autoupdate_hooks_executes_successfully_with_repos(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    test_repos = ["some-repo-url"]
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
        execute_result = pre_commit.autoupdate_hooks(test_folder_path, repos=test_repos)

        assert execute_result.successful
        assert "--repo some-repo-url" in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_autoupdate_hooks_executes_successfully_with_multiple_repos(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    test_repos = ["some-repo-url", "some-other-repo-url"]
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        execute_result = pre_commit.autoupdate_hooks(test_folder_path, repos=test_repos)

        assert execute_result.successful
        assert "--repo some-repo-url" in mock_subprocess.run.call_args_list[0].args[0]
        assert (
            "--repo some-other-repo-url"
            in mock_subprocess.run.call_args_list[0].args[0]
        )


def test_that_pre_commit_autoupdate_hooks_fails_with_repos_containing_non_strings(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    test_repos = [{"something": "something-else"}]
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        execute_result = pre_commit.autoupdate_hooks(test_folder_path, repos=test_repos)

        assert not execute_result.successful


def test_that_pre_commit_autoupdate_hooks_ignores_repos_when_repos_is_a_dict(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    test_repos = {}
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        execute_result = pre_commit.autoupdate_hooks(test_folder_path, repos=test_repos)  # type: ignore

        assert execute_result.successful
        assert "--repo {}" not in mock_subprocess.run.call_args_list[0].args[0]


def test_that_pre_commit_autoupdate_hooks_converts_repos_when_repos_is_a_string(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    test_repos = "string"
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        execute_result = pre_commit.autoupdate_hooks(test_folder_path, repos=test_repos)  # type: ignore

        assert execute_result.successful
        assert "--repo string" in mock_subprocess.run.call_args_list[0].args[0]


##### update #####
def test_that_pre_commit_update_executes_successfully(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        execute_result = pre_commit.update(test_folder_path)

        assert execute_result.successful


def test_that_pre_commit_update_properly_handles_failed_executions(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        execute_result = pre_commit.update(test_folder_path)

        assert not execute_result.successful


##### remove_unused_hooks #####
def test_that_pre_commit_remove_unused_hookss_executes_successfully(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=0)
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        execute_result = pre_commit.remove_unused_hooks(test_folder_path)

        assert execute_result.successful


def test_that_pre_commit_remove_unused_hooks_properly_handles_failed_executions(
    pre_commit: PreCommitAbstraction,
    mock_subprocess: MagicMock,
):
    mock_subprocess.run.return_value = CompletedProcess(args=[], returncode=1)
    with (um.patch.object(Path, "exists") as mock_exists,):
        mock_exists.return_value = True
        execute_result = pre_commit.remove_unused_hooks(test_folder_path)

        assert not execute_result.successful


def test_that_pre_commit_install_creates_pre_commit_hook_for_secureli(
    pre_commit: PreCommitAbstraction,
):
    with (
        um.patch("builtins.open", um.mock_open()) as mock_open,
        um.patch.object(Path, "exists") as mock_exists,
        um.patch.object(Path, "chmod") as mock_chmod,
        um.patch.object(Path, "stat"),
        um.patch.object(Path, "is_file") as mock_is_file,
        um.patch.object(shutil, "copy2") as mock_copy,
    ):
        mock_exists.return_value = True
        mock_is_file.return_value = False

        mock_is_file.return_value = False

        result = pre_commit.install(test_folder_path)

        assert result == InstallResult(successful=True, backup_hook_path=None)
        mock_open.assert_called_once()
        mock_chmod.assert_called_once()
        mock_copy.assert_not_called()


def test_that_pre_commit_install_creates_backup_file_when_already_exists(
    pre_commit: PreCommitAbstraction,
):
    mock_backup_datetime = datetime.datetime(2024, 1, 1, 6, 30, 45)
    with (
        um.patch("builtins.open", um.mock_open()),
        um.patch.object(Path, "is_file") as mock_is_file,
        um.patch.object(Path, "chmod"),
        um.patch.object(Path, "stat"),
        um.patch.object(shutil, "copy2") as mock_copy,
        um.patch("datetime.datetime") as mock_dt,
    ):
        mock_is_file.return_value = True
        mock_dt.now.return_value = mock_backup_datetime

        result = pre_commit.install(test_folder_path)

        assert result.successful == True
        assert (
            "/.git/hooks/pre-commit.backup.20240101T063045" in result.backup_hook_path
        )
        mock_is_file.assert_called_once()
        mock_copy.assert_called_once()


def test_pre_commit_config_file_is_deserialized_correctly(
    pre_commit: PreCommitAbstraction,
):
    with (
        um.patch("builtins.open", um.mock_open()) as mock_open,
        um.patch.object(Path, "exists") as mock_exists,
    ):
        mock_exists.return_value = True
        mock_open.return_value.read.return_value = (
            "repos:\n"
            "  - repo: my-repo\n"
            "    rev: tag1\n"
            "    hooks:\n"
            "      - id: detect-secrets\n"
            "        args: ['--foo', '--bar']\n"
        )
        pre_commit_config = pre_commit.get_pre_commit_config(test_folder_path)
        assert pre_commit_config.repos[0].url == "my-repo"
        assert pre_commit_config.repos[0].rev == "tag1"
        assert pre_commit_config.repos[0].hooks[0].id == "detect-secrets"


@pytest.mark.parametrize(
    argnames=["rev", "rev_is_sha"], argvalues=[("tag1", False), (example_git_sha, True)]
)
def test_check_for_hook_updates_infers_freeze_param_when_not_provided(
    pre_commit: PreCommitAbstraction,
    rev: str,
    rev_is_sha: bool,
):
    with um.patch(
        "secureli.abstractions.pre_commit.HookRepoRevInfo.from_config"
    ) as mock_hook_repo_rev_info:
        pre_commit_config_repo = PreCommitRepo(
            repo="http://example-repo.com/",
            rev=rev,
            hooks=[PreCommitHook(id="hook-id")],
        )
        pre_commit_config = PreCommitSettings(repos=[pre_commit_config_repo])
        rev_info_mock = MagicMock(rev=pre_commit_config_repo.rev)
        mock_hook_repo_rev_info.return_value = rev_info_mock
        rev_info_mock.update.return_value = rev_info_mock  # Returning the same revision info on update means the hook will be considered up to date
        pre_commit.check_for_hook_updates(pre_commit_config)
        rev_info_mock.update.assert_called_with(tags_only=True, freeze=rev_is_sha)


def test_check_for_hook_updates_respects_freeze_param_when_false(
    pre_commit: PreCommitAbstraction,
):
    """
    When freeze is explicitly provided, the rev_info.update() method respect that value
    regardless of whether the existing rev is a tag or a commit hash.
    """
    with um.patch(
        "secureli.abstractions.pre_commit.HookRepoRevInfo.from_config"
    ) as mock_hook_repo_rev_info:
        pre_commit_config_repo = PreCommitRepo(
            repo="http://example-repo.com/",
            rev=example_git_sha,
            hooks=[PreCommitHook(id="hook-id")],
        )
        pre_commit_config = PreCommitSettings(repos=[pre_commit_config_repo])
        rev_info_mock = MagicMock(rev=pre_commit_config_repo.rev)
        mock_hook_repo_rev_info.return_value = rev_info_mock
        rev_info_mock.update.return_value = rev_info_mock  # Returning the same revision info on update means the hook will be considered up to date
        pre_commit.check_for_hook_updates(pre_commit_config, freeze=False)
        rev_info_mock.update.assert_called_with(tags_only=True, freeze=False)


def test_check_for_hook_updates_respects_freeze_param_when_true(
    pre_commit: PreCommitAbstraction,
):
    with um.patch(
        "secureli.abstractions.pre_commit.HookRepoRevInfo.from_config"
    ) as mock_hook_repo_rev_info:
        pre_commit_config_repo = PreCommitRepo(
            repo="http://example-repo.com/",
            rev="tag1",
            hooks=[PreCommitHook(id="hook-id")],
        )
        pre_commit_config = PreCommitSettings(repos=[pre_commit_config_repo])
        rev_info_mock = MagicMock(rev=pre_commit_config_repo.rev)
        mock_hook_repo_rev_info.return_value = rev_info_mock
        rev_info_mock.update.return_value = rev_info_mock  # Returning the same revision info on update means the hook will be considered up to date
        pre_commit.check_for_hook_updates(pre_commit_config, freeze=True)
        rev_info_mock.update.assert_called_with(tags_only=True, freeze=True)


def test_check_for_hook_updates_returns_repos_with_new_revs(
    pre_commit: PreCommitAbstraction,
):
    with um.patch(
        "secureli.abstractions.pre_commit.HookRepoRevInfo"
    ) as mock_hook_repo_rev_info:
        repo_urls = ["http://example-repo.com/", "http://example-repo-2.com/"]
        old_rev = "tag1"
        repo_1_new_rev = "tag2"
        pre_commit_config = PreCommitSettings(
            repos=[
                PreCommitRepo(
                    repo=repo_url, rev=old_rev, hooks=[PreCommitHook(id="hook-id")]
                )
                for repo_url in repo_urls
            ]
        )
        repo_1_old_rev_mock = MagicMock(rev=old_rev, repo=repo_urls[0])
        repo_1_new_rev_mock = MagicMock(rev=repo_1_new_rev, repo=repo_urls[0])
        repo_2_old_rev_mock = MagicMock(rev=old_rev, repo=repo_urls[1])
        mock_hook_repo_rev_info.from_config = MagicMock(
            side_effect=[repo_1_old_rev_mock, repo_2_old_rev_mock]
        )
        repo_1_old_rev_mock.update.return_value = repo_1_new_rev_mock
        repo_2_old_rev_mock.update.return_value = (
            repo_2_old_rev_mock  # this update should return the same rev info
        )
        updated_repos = pre_commit.check_for_hook_updates(pre_commit_config)
        assert len(updated_repos) == 1  # only the first repo should be returned
        assert updated_repos[repo_urls[0]].oldRev == "tag1"
        assert updated_repos[repo_urls[0]].newRev == "tag2"


def test_pre_commit_config_exists(pre_commit: PreCommitAbstraction):
    with um.patch.object(Path, "exists", return_value=True):
        pre_commit_exists = pre_commit.pre_commit_config_exists(test_folder_path)
        assert pre_commit_exists == True


def test_pre_commit_config_does_not_exist(pre_commit: PreCommitAbstraction):
    with um.patch.object(Path, "exists", return_value=False):
        pre_commit_exists = pre_commit.pre_commit_config_exists(test_folder_path)
        assert pre_commit_exists == False


def test_get_pre_commit_config_path_returns_correct_location(
    pre_commit: PreCommitAbstraction,
):
    with um.patch.object(Path, "exists", return_value=True):
        pre_commit_config_path = pre_commit.get_pre_commit_config_path(test_folder_path)
        assert pre_commit_config_path == PosixPath(
            f"{test_folder_path}/.secureli/.pre-commit-config.yaml"
        )

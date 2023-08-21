import stat
import subprocess
from pathlib import Path

from typing import Optional

import pydantic


class InstallFailedError(Exception):
    """Attempting to invoke pre-commit to set up our repo for the given template did not succeed"""

    pass


class ExecuteFailedError(Exception):
    """Attempting to invoke pre-commit to test our repo did not succeed"""

    pass


class InstallLanguageConfigError(Exception):
    """Attempting to install language specific config to .secureli was not successful"""

    pass


class ExecuteResult(pydantic.BaseModel):
    """
    The results of calling execute_hooks
    """

    successful: bool
    output: str


class InstallResult(pydantic.BaseModel):
    """
    The results of calling install
    """

    successful: bool
    # version_installed: str


class PreCommitAbstraction:
    """
    Abstracts the configuring and execution of pre-commit.
    """

    def __init__(
        self,
        command_timeout_seconds: int,
    ):
        self.command_timeout_seconds = command_timeout_seconds

    def install(self, folder_path: Path):
        """
        Creates the pre-commit hook file in the .git directory so that `secureli scan` is run on each commit
        """

        # Write pre-commit with invocation of `secureli scan`
        pre_commit_hook = folder_path / ".git/hooks/pre-commit"
        with open(pre_commit_hook, "w") as f:
            f.write("#!/bin/sh\n")
            f.write("secureli scan\n")

        # Make pre-commit executable
        pre_commit_hook.chmod(pre_commit_hook.stat().st_mode | stat.S_IEXEC)

    def execute_hooks(
        self, folder_path: Path, all_files: bool = False, hook_id: Optional[str] = None
    ) -> ExecuteResult:
        """
        Execute the configured hooks against the repository, either against your staged changes
        or all the files in the repo
        :param folder_path: Indicates the git folder against which you run secureli
        :param all_files: True if we want to scan all files, default to false, which only
        scans our staged changes we're about to commit
        :param hook_id: A specific hook to run. If None, all hooks will be run
        :return: ExecuteResult, indicating success or failure.
        """
        # always log colors so that we can print them out later, which does not happen by default
        # when we capture the output (which we do so we can add it to our logs).
        subprocess_args = [
            "pre-commit",
            "run",
            "--color",
            "always",
        ]
        if all_files:
            subprocess_args.append("--all-files")

        if hook_id:
            subprocess_args.append(hook_id)

        completed_process = subprocess.run(
            subprocess_args, stdout=subprocess.PIPE, cwd=folder_path
        )
        output = (
            completed_process.stdout.decode("utf8") if completed_process.stdout else ""
        )
        if completed_process.returncode != 0:
            return ExecuteResult(successful=False, output=output)
        else:
            return ExecuteResult(successful=True, output=output)

    def autoupdate_hooks(
        self,
        folder_path: Path,
        bleeding_edge: bool = False,
        freeze: bool = False,
        repos: Optional[list] = None,
    ) -> ExecuteResult:
        """
        Updates the precommit hooks but executing precommit's autoupdate command.  Additional info at
        https://pre-commit.com/#pre-commit-autoupdate
        :param folder_path: Indicates the git folder against which you run secureli
        :param bleeding_edge: True if updating to the bleeding edge of the default branch instead of
        the latest tagged version (which is the default behavior)
        :param freeze: Set to True to store "frozen" hashes in rev instead of tag names.
        :param repos: List of repos (url as a string) to update. This is used to target specific repos instead of all repos.
        :return: ExecuteResult, indicating success or failure.
        """
        subprocess_args = [
            "pre-commit",
            "autoupdate",
        ]
        if bleeding_edge:
            subprocess_args.append("--bleeding-edge")

        if freeze:
            subprocess_args.append("--freeze")

        if repos:
            repo_args = []

            if isinstance(repos, str):
                # If a string is passed in, converts to a list containing the string
                repos = [repos]

            for repo in repos:
                if isinstance(repo, str):
                    arg = "--repo {}".format(repo)
                    repo_args.append(arg)
                else:
                    output = "Unable to update repo, string validation failed. Repo parameter should be a dictionary of strings."
                    return ExecuteResult(successful=False, output=output)

            subprocess_args.extend(repo_args)

        completed_process = subprocess.run(
            subprocess_args, stdout=subprocess.PIPE, cwd=folder_path
        )
        output = (
            completed_process.stdout.decode("utf8") if completed_process.stdout else ""
        )
        if completed_process.returncode != 0:
            return ExecuteResult(successful=False, output=output)
        else:
            return ExecuteResult(successful=True, output=output)

    def update(self, folder_path: Path) -> ExecuteResult:
        """
        Installs the hooks defined in pre-commit-config.yml.
        :param folder_path: Indicates the git folder against which you run secureli
        :return: ExecuteResult, indicating success or failure.
        """
        subprocess_args = ["pre-commit", "install-hooks", "--color", "always"]

        completed_process = subprocess.run(
            subprocess_args, stdout=subprocess.PIPE, cwd=folder_path
        )
        output = (
            completed_process.stdout.decode("utf8") if completed_process.stdout else ""
        )
        if completed_process.returncode != 0:
            return ExecuteResult(successful=False, output=output)
        else:
            return ExecuteResult(successful=True, output=output)

    def remove_unused_hooks(self, folder_path: Path) -> ExecuteResult:
        """
        Removes unused hook repos from the cache.  Pre-commit determines which flags are "unused" by comparing
        the repos to the pre-commit-config.yaml file.  Any cached hook repos that are not in the config file
        will be removed from the cache.
        :param folder_path: Indicates the git folder against which you run secureli
        :return: ExecuteResult, indicating success or failure.
        """
        subprocess_args = ["pre-commit", "gc", "--color", "always"]

        completed_process = subprocess.run(
            subprocess_args, stdout=subprocess.PIPE, cwd=folder_path
        )
        output = (
            completed_process.stdout.decode("utf8") if completed_process.stdout else ""
        )
        if completed_process.returncode != 0:
            return ExecuteResult(successful=False, output=output)
        else:
            return ExecuteResult(successful=True, output=output)

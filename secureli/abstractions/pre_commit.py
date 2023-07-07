import subprocess

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

    def install(self, language: str) -> InstallResult:
        """
        Identifies the template we hold for the specified language, writes it, installs it, and cleans up
        :param language: The language to identify a template for
        :raises LanguageNotSupportedError if a pre-commit template cannot be found for the specified language
        :raises InstallFailedError if the template was found, but an error occurred installing it
        """

        completed_process = subprocess.run(["pre-commit", "install"])
        if completed_process.returncode != 0:
            raise InstallFailedError(
                f"Installing the pre-commit script for {language} failed"
            )

        # install_configs_result = self._install_pre_commit_configs(language)

        return InstallResult(
            successful=True,
            # version_installed=language_config.version,
        )

    def execute_hooks(
        self, all_files: bool = False, hook_id: Optional[str] = None
    ) -> ExecuteResult:
        """
        Execute the configured hooks against the repository, either against your staged changes
        or all the files in the repo
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

        completed_process = subprocess.run(subprocess_args, stdout=subprocess.PIPE)
        output = (
            completed_process.stdout.decode("utf8") if completed_process.stdout else ""
        )
        if completed_process.returncode != 0:
            return ExecuteResult(successful=False, output=output)
        else:
            return ExecuteResult(successful=True, output=output)

    def autoupdate_hooks(
        self,
        bleeding_edge: bool = False,
        freeze: bool = False,
        repos: Optional[list] = None,
    ) -> ExecuteResult:
        """
        Updates the precommit hooks but executing precommit's autoupdate command.  Additional info at
        https://pre-commit.com/#pre-commit-autoupdate
        :param bleeding edge: True if updating to the bleeding edge of the default branch instead of
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

        completed_process = subprocess.run(subprocess_args, stdout=subprocess.PIPE)
        output = (
            completed_process.stdout.decode("utf8") if completed_process.stdout else ""
        )
        if completed_process.returncode != 0:
            return ExecuteResult(successful=False, output=output)
        else:
            return ExecuteResult(successful=True, output=output)

    def update(self) -> ExecuteResult:
        """
        Installs the hooks defined in pre-commit-config.yml.
        :return: ExecuteResult, indicating success or failure.
        """
        subprocess_args = ["pre-commit", "install-hooks", "--color", "always"]

        completed_process = subprocess.run(subprocess_args, stdout=subprocess.PIPE)
        output = (
            completed_process.stdout.decode("utf8") if completed_process.stdout else ""
        )
        if completed_process.returncode != 0:
            return ExecuteResult(successful=False, output=output)
        else:
            return ExecuteResult(successful=True, output=output)

    def remove_unused_hooks(self) -> ExecuteResult:
        """
        Removes unused hook repos from the cache.  Pre-commit determines which flags are "unused" by comparing
        the repos to the pre-commit-config.yaml file.  Any cached hook repos that are not in the config file
        will be removed from the cache.
        :return: ExecuteResult, indicating success or failure.
        """
        subprocess_args = ["pre-commit", "gc", "--color", "always"]

        completed_process = subprocess.run(subprocess_args, stdout=subprocess.PIPE)
        output = (
            completed_process.stdout.decode("utf8") if completed_process.stdout else ""
        )
        if completed_process.returncode != 0:
            return ExecuteResult(successful=False, output=output)
        else:
            return ExecuteResult(successful=True, output=output)

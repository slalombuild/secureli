from pathlib import Path
from typing import Optional

from secureli.utilities.usage_stats import post_log, convert_failures_to_failure_count
from secureli.abstractions.echo import EchoAbstraction
from secureli.services.logging import LoggingService, LogAction
from secureli.services.scanner import (
    ScanMode,
    ScannerService,
    Failure,
    OutputParseErrors,
)
from secureli.actions.action import VerifyOutcome, Action, ActionDependencies
from secureli.repositories.settings import (
    SecureliRepository,
    SecureliFile,
    PreCommitSettings,
    PreCommitRepo,
    PreCommitHook,
)
import json


class ScanAction(Action):
    """The action for the secureli `scan` command, orchestrating services and outputs results"""

    """Any verification outcomes that would cause us to not proceed to scan."""
    halting_outcomes = [
        VerifyOutcome.INSTALL_FAILED,
        VerifyOutcome.INSTALL_CANCELED,
    ]

    def __init__(
        self,
        action_deps: ActionDependencies,
        echo: EchoAbstraction,
        logging: LoggingService,
        scanner: ScannerService,
        # settings_repository: SecureliRepository,
    ):
        super().__init__(action_deps)
        self.scanner = scanner
        self.echo = echo
        self.logging = logging
        # self.settings = settings_repository

    def scan_repo(
        self,
        folder_path: Path,
        scan_mode: ScanMode,
        always_yes: bool,
        specific_test: Optional[str] = None,
    ):
        """
        Scans the given directory, or offers to go through initialization if that has not
        been completed yet. Also detects if we're out of date with SeCureLI's config
        for the language and offers to upgrade (though continues on if the user says no)
        :param folder_path: The folder path to initialize the repo for
        :param scan_mode: How we should scan the files in the repo (i.e. staged only or all)
        :param always_yes: Assume "Yes" to all prompts
        :param specific_test: If set, limits scanning to the single pre-commit hook.
        Otherwise, scans with all hooks.
        """
        verify_result = self.verify_install(folder_path, False, always_yes)

        if verify_result.outcome in self.halting_outcomes:
            return

        scan_result = self.scanner.scan_repo(scan_mode, specific_test)

        details = scan_result.output or "Unknown output during scan"
        self.echo.print(details)

        failure_count = len(scan_result.failures)
        scan_result_failures_json_string = json.dumps(
            [ob.__dict__ for ob in scan_result.failures]
        )

        individual_failure_count = convert_failures_to_failure_count(
            scan_result.failures
        )

        if failure_count > 0:
            self._process_failures(scan_result.failures, always_yes=always_yes)

        if not scan_result.successful:
            log_data = self.logging.failure(
                LogAction.scan,
                scan_result_failures_json_string,
                failure_count,
                individual_failure_count,
            )

            post_log(log_data.json(exclude_none=True))
        else:
            self.echo.print("Scan executed successfully and detected no issues!")
            log_data = self.logging.success(LogAction.scan)

            post_log(log_data.json(exclude_none=True))

    def _process_failures(
        self,
        failures: list[Failure],
        always_yes: bool,
    ):
        """
        Processes any failures found during the scan.
        :param failures: List of Failure objects representing linter failures
        :param always_yes: Assume "Yes" to all prompts
        """
        settings = self.action_deps.settings.load()

        ignore_fail_prompt = "Failures detected during scan.\n"
        ignore_fail_prompt += "Add an ignore rule?"

        # Ask if the user wants to ignore a failure
        if always_yes:
            always_yes_warning = "Hook failures were detected but the scan was initiated with the 'yes' flag.\n"
            always_yes_warning += "SeCureLI cannot automatically add ignore rules with the 'yes' flag enabled.\n"
            always_yes_warning += "Re-run your scan without the 'yes' flag to add an ignore rule for one of the\n"
            always_yes_warning += "detected failures."

            self.echo.print(always_yes_warning)
        elif self.echo.confirm(ignore_fail_prompt, default_response=False):
            # verify pre_commit exists in settings file.
            if not settings.pre_commit:
                settings.pre_commit = PreCommitSettings()

            for failure in failures:
                add_ignore_for_id = self.echo.confirm(
                    "\nWould you like to add an ignore for the {} failure on {}?".format(
                        failure.id, failure.file
                    )
                )
                if failure.repo == OutputParseErrors.REPO_NOT_FOUND:
                    self._handle_repo_not_found(failure)
                elif always_yes or add_ignore_for_id:
                    settings = self._add_ignore_for_failure(
                        failure=failure, always_yes=always_yes, settings_file=settings
                    )

            self.action_deps.settings.save(settings=settings)

    def _add_ignore_for_failure(
        self,
        failure: Failure,
        always_yes: bool,
        settings_file: SecureliFile,
    ):
        """
        Processes an individual failure and adds an ignore rule for either the entire
        hook or a particular file.
        :param failure: Failure object representing a rule failure during a scan
        :param always_yes: Assume "Yes" to all prompts
        :param settings_file: SecureliFile representing the contents of the .secureli.yaml file
        """
        ignore_repo_prompt = "You can add an ignore rule for just this file, or you can add an ignore rule for all files.\n"
        ignore_repo_prompt += (
            "Would you like to ignore this failure for all files?".format(failure.id)
        )
        ignore_file_prompt = (
            "\nWould you like to ignore this failure for just the {} file?".format(
                failure.file
            )
        )

        self.echo.print("\nAdding an ignore rule for: {}\n".format(failure.id))

        if always_yes or self.echo.confirm(
            message=ignore_repo_prompt, default_response=False
        ):
            # ignore for all files
            self.echo.print("Adding an ignore for all files.")
            modified_settings = self._ignore_all_files(
                failure=failure, settings_file=settings_file
            )
        else:
            if always_yes or self.echo.confirm(ignore_file_prompt, False):
                self.echo.print("Adding an ignore for {}".format(failure.file))
                modified_settings = self._ignore_one_file(
                    failure=failure, settings_file=settings_file
                )
            else:
                self.echo.print(
                    "\nSkipping {} failure on {}".format(failure.id, failure.file)
                )
                modified_settings = settings_file

        return modified_settings

    def _handle_repo_not_found(self, failure: Failure):
        """
        Handles a REPO_NOT_FOUND error
        :param failure: A Failure object representing the scan failure with a missing repo url
        """
        id = failure.id
        self.echo.print(
            "Unable to add an ignore for {}, SeCureLI was unable to identify the repo it belongs to.".format(
                failure.id
            )
        )
        self.echo.print("Skipping {}".format(id))

    def _ignore_all_files(self, failure: Failure, settings_file: SecureliFile):
        """
        Supresses a hook for all files in this repo
        :param failure: Failure object representing the failed hook
        :param settings_file: SecureliFile representing the contents of the .secureli.yaml file
        :return: Returns the settings file after modifications
        """
        pre_commit_settings = settings_file.pre_commit
        repos = pre_commit_settings.repos
        repo_settings_index = next(
            (index for (index, repo) in enumerate(repos) if repo.url == failure.repo),
            None,
        )

        if repo_settings_index is not None:
            repo_settings = pre_commit_settings.repos[repo_settings_index]
            if failure.id not in repo_settings.suppressed_hook_ids:
                repo_settings.suppressed_hook_ids.append(failure.id)
        else:
            repo_settings = PreCommitRepo(
                url=failure.repo, suppressed_hook_ids=[failure.id]
            )
            repos.append(repo_settings)

        self.echo.print(
            "Added {} to the suppressed_hooks_ids list for the {} repo".format(
                failure.id, failure.repo
            )
        )

        return settings_file

    def _ignore_one_file(self, failure: Failure, settings_file: SecureliFile):
        """
        Adds the failed file to the file exemptions list for the failed hook
         :param failure: Failure object representing the failed hook
         :param settings_file: SecureliFile representing the contents of the .secureli.yaml file
        """
        pre_commit_settings = settings_file.pre_commit
        repos = pre_commit_settings.repos
        repo_settings_index = next(
            (index for (index, repo) in enumerate(repos) if repo.url == failure.repo),
            None,
        )

        if repo_settings_index is not None:
            repo_settings = pre_commit_settings.repos[repo_settings_index]
        else:
            repo_settings = PreCommitRepo(url=failure.repo)
            repos.append(repo_settings)

        hooks = repo_settings.hooks
        hook_settings_index = next(
            (index for (index, hook) in enumerate(hooks) if hook.id == failure.id),
            None,
        )

        if hook_settings_index is not None:
            hook_settings = hooks[hook_settings_index]
            if failure.file not in hook_settings.exclude_file_patterns:
                hook_settings.exclude_file_patterns.append(failure.file)
            else:
                self.echo.print(
                    "An ignore rule is already present for the {} file".format(
                        failure.file
                    )
                )
        else:
            hook_settings = PreCommitHook(id=failure.id)
            hook_settings.exclude_file_patterns.append(failure.file)
            repo_settings.hooks.append(hook_settings)

        return settings_file

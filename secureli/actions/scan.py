import json
import sys
from pathlib import Path
from time import time
from typing import Optional

from secureli.abstractions.echo import EchoAbstraction
from secureli.actions.action import (
    VerifyOutcome,
    Action,
    ActionDependencies,
    VerifyResult,
)
from secureli.models.exit_codes import ExitCode
from secureli.models.publish_results import PublishResultsOption
from secureli.models.result import Result
from secureli.services.logging import LoggingService, LogAction
from secureli.services.scanner import (
    ScanMode,
    ScannerService,
)
from secureli.settings import Settings
from secureli.utilities.usage_stats import post_log, convert_failures_to_failure_count

ONE_WEEK_IN_SECONDS: int = 7 * 24 * 60 * 60


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
    ):
        super().__init__(action_deps)
        self.scanner = scanner
        self.echo = echo
        self.logging = logging

    def _check_secureli_hook_updates(self, folder_path: Path) -> VerifyResult:
        """
        Queries repositories referenced by pre-commit hooks to check
        if we have the latest revisions listed in the .pre-commit-config.yaml file
        :param folder_path: The folder path containing the .pre-commit-config.yaml file
        """

        self.action_deps.echo.info("Checking for pre-commit hook updates...")
        pre_commit_config = self.scanner.pre_commit.get_pre_commit_config(folder_path)

        repos_to_update = self.scanner.pre_commit.check_for_hook_updates(
            pre_commit_config
        )

        if not repos_to_update:
            self.action_deps.echo.info("No hooks to update")
            return VerifyResult(outcome=VerifyOutcome.UP_TO_DATE)

        for repo, revs in repos_to_update.items():
            self.action_deps.echo.debug(
                f"Found update for {repo}: {revs.oldRev} -> {revs.newRev}"
            )
        self.action_deps.echo.warning(
            "You have out-of-date pre-commit hooks. Run `secureli update` to update them."
        )
        # Since we don't actually perform the updates here, return an outcome of UPDATE_CANCELLED
        return VerifyResult(outcome=VerifyOutcome.UPDATE_CANCELED)

    def publish_results(
        self,
        publish_results_condition: PublishResultsOption,
        action_successful: bool,
        log_str: str,
    ):
        """
        Publish the results of the scan to the configured observability platform
        :param publish_results_condition: When to publish the results of the scan to the configured observability platform
        :param action_successful: Whether we should publish a success or failure
        :param log_str: a string to be POSTed to backend instrumentation
        """
        if publish_results_condition == PublishResultsOption.ALWAYS or (
            publish_results_condition == PublishResultsOption.ON_FAIL
            and not action_successful
        ):
            result = post_log(log_str, Settings())
            self.echo.debug(result.result_message)

            if result.result == Result.SUCCESS:
                self.logging.success(LogAction.publish)
            else:
                self.logging.failure(LogAction.publish, result.result_message)

    def scan_repo(
        self,
        folder_path: Path,
        scan_mode: ScanMode,
        always_yes: bool,
        publish_results_condition: PublishResultsOption = PublishResultsOption.NEVER,
        specific_test: Optional[str] = None,
        files: Optional[str] = None,
    ):
        """
        Scans the given directory, or offers to go through initialization if that has not
        been completed yet. Also detects if we're out of date with seCureLI's config
        for the language and offers to upgrade (though continues on if the user says no)
        :param folder_path: The folder path to initialize the repo for
        :param scan_mode: How we should scan the files in the repo (i.e. staged only or all)
        :param always_yes: Assume "Yes" to all prompts
        :param specific_test: If set, limits scanning to the single pre-commit hook.
        Otherwise, scans with all hooks.
        """
        verify_result = self.verify_install(folder_path, False, always_yes)

        # Check if pre-commit hooks are up-to-date
        secureli_config = self.action_deps.secureli_config.load()
        now: int = int(time())
        if (secureli_config.last_hook_update_check or 0) + ONE_WEEK_IN_SECONDS < now:
            self._check_secureli_hook_updates(folder_path)
            secureli_config.last_hook_update_check = now
            self.action_deps.secureli_config.save(secureli_config)

        if verify_result.outcome in self.halting_outcomes:
            return

        scan_result = self.scanner.scan_repo(
            folder_path, scan_mode, specific_test, files=files
        )

        details = scan_result.output or "Unknown output during scan"
        self.echo.print(details)

        failure_count = len(scan_result.failures)
        scan_result_failures_json_string = json.dumps(
            [ob.__dict__ for ob in scan_result.failures]
        )

        individual_failure_count = convert_failures_to_failure_count(
            scan_result.failures
        )

        log_data = (
            self.logging.success(LogAction.scan)
            if scan_result.successful
            else self.logging.failure(
                LogAction.scan,
                scan_result_failures_json_string,
                failure_count,
                individual_failure_count,
            )
        )
        self.publish_results(
            publish_results_condition,
            action_successful=scan_result.successful,
            log_str=log_data.json(exclude_none=True),
        )
        if scan_result.successful:
            self.echo.print("Scan executed successfully and detected no issues!")
        else:
            sys.exit(ExitCode.SCAN_ISSUES_DETECTED.value)

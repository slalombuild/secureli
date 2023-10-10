import json
import sys
from pathlib import Path
from typing import Optional

from secureli.abstractions.echo import EchoAbstraction
from secureli.actions.action import VerifyOutcome, Action, ActionDependencies
from secureli.services.logging import LoggingService, LogAction
from secureli.services.scanner import (
    ScanMode,
    ScannerService,
)
from secureli.utilities.usage_stats import post_log, convert_failures_to_failure_count


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

    def scan_repo(
        self,
        folder_path: Path,
        scan_mode: ScanMode,
        always_yes: bool,
        specific_test: Optional[str] = None,
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

        if verify_result.outcome in self.halting_outcomes:
            return

        scan_result = self.scanner.scan_repo(folder_path, scan_mode, specific_test)

        details = scan_result.output or "Unknown output during scan"
        self.echo.print(details)

        failure_count = len(scan_result.failures)
        scan_result_failures_json_string = json.dumps(
            [ob.__dict__ for ob in scan_result.failures]
        )

        individual_failure_count = convert_failures_to_failure_count(
            scan_result.failures
        )

        if not scan_result.successful:
            log_data = self.logging.failure(
                LogAction.scan,
                scan_result_failures_json_string,
                failure_count,
                individual_failure_count,
            )

            post_log(log_data.json(exclude_none=True))
            sys.exit("Issues Found...Aborting")
        else:
            self.echo.print("Scan executed successfully and detected no issues!")
            log_data = self.logging.success(LogAction.scan)

            post_log(log_data.json(exclude_none=True))

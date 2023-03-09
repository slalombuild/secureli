from pathlib import Path
from typing import Optional

from secureli.abstractions.echo import EchoAbstraction
from secureli.services.logging import LoggingService, LogAction
from secureli.services.scanner import ScanMode, ScannerService
from secureli.actions.action import VerifyOutcome, Action, ActionDependencies


class ScanAction(Action):
    """The action for the secureli `scan` command, orchestrating services and outputs results"""

    """Any verification outcomes that would cause us to not proceed to scan."""
    halting_outcomes = [
        VerifyOutcome.INSTALL_FAILED,
        VerifyOutcome.INSTALL_CANCELED,
        VerifyOutcome.UPGRADE_CANCELED,
        VerifyOutcome.UPGRADE_FAILED,
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
        if not scan_result.successful:
            self.echo.print(details)
            self.logging.failure(LogAction.scan, details)
        else:
            self.echo.print("Scan executed successfully and detected no issues!")
            self.logging.success(LogAction.scan)

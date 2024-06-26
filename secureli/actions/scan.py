import json
import sys
from pathlib import Path
from time import time
from typing import Optional

from secureli.modules.custom_scanners.custom_scans import CustomScannersService
from secureli.actions import action
from secureli.modules.shared.abstractions.version_control_repo import (
    VersionControlRepoAbstraction,
)
from secureli.modules.shared.models.exit_codes import ExitCode
from secureli.modules.shared.models import install
from secureli.modules.shared.models.logging import LogAction
from secureli.modules.shared.models.publish_results import PublishResultsOption
from secureli.modules.shared.models.result import Result
from secureli.modules.core.core_services.hook_scanner import HooksScannerService
from secureli.modules.shared.models.scan import ScanMode
from secureli.settings import Settings
from secureli.modules.shared import utilities

ONE_WEEK_IN_SECONDS: int = 7 * 24 * 60 * 60


class ScanAction(action.Action):
    """The action for the secureli `scan` command, orchestrating services and outputs results"""

    """Any verification outcomes that would cause us to not proceed to scan."""
    halting_outcomes = [
        install.VerifyOutcome.INSTALL_FAILED,
        install.VerifyOutcome.INSTALL_CANCELED,
        install.VerifyOutcome.UPDATE_FAILED,
        install.VerifyOutcome.UPDATE_CANCELED,
    ]

    def __init__(
        self,
        action_deps: action.ActionDependencies,
        hooks_scanner: HooksScannerService,
        custom_scanners: CustomScannersService,
        file_repo: VersionControlRepoAbstraction,
    ):
        super().__init__(action_deps)
        self.hooks_scanner = hooks_scanner
        self.custom_scanners = custom_scanners
        self.file_repo = file_repo

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
            result = utilities.post_log(log_str, Settings())
            self.action_deps.echo.debug(result.result_message)

            if result.result == Result.SUCCESS:
                self.action_deps.logging.success(LogAction.publish)
            else:
                self.action_deps.logging.failure(
                    LogAction.publish, result.result_message
                )

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
        :param specific_test: If set, limits scanning to the single pre-commit hook or custom scan.
        :param files: If set, scans only the files provided.
        Otherwise, scans with all hooks.
        """

        scan_files = [Path(file) for file in files or []] or self._get_commited_files(
            scan_mode, folder_path
        )
        verify_result = self.verify_install(
            folder_path,
            False,
            always_yes,
            scan_files,
            action_source=install.ActionSource.SCAN,
        )

        # Check if pre-commit hooks are up-to-date
        secureli_config = self.action_deps.secureli_config.load()
        now: int = int(time())
        if (secureli_config.last_hook_update_check or 0) + ONE_WEEK_IN_SECONDS < now:
            self._check_secureli_hook_updates(folder_path)
            secureli_config.last_hook_update_check = now
            self.action_deps.secureli_config.save(secureli_config)

        if verify_result.outcome in self.halting_outcomes:
            return

        # Execute custom scans
        custom_scan_results = None
        custom_scan_results = self.custom_scanners.scan_repo(
            folder_path, scan_mode, specific_test, files=files
        )

        """
        Execute hooks only if no custom scan results were returned or if running all scans.
        If a hook and custom scan exist with the same id, only the custom scan will run.
        Without this check, if we specify a non-existant pre-commit hook id but a valid custom scan id,
        the final result won't be succesful as the pre-commit command will exit with return code 1.
        """
        hooks_scan_results = None
        if custom_scan_results is None or specific_test is None:
            hooks_scan_results = self.hooks_scanner.scan_repo(
                folder_path, scan_mode, specific_test, files=files
            )

        scan_result = utilities.merge_scan_results(
            [custom_scan_results, hooks_scan_results]
        )

        details = scan_result.output or "Unknown output during scan"
        self.action_deps.echo.print(details)

        failure_count = len(scan_result.failures)
        scan_result_failures_json_string = json.dumps(
            [ob.__dict__ for ob in scan_result.failures]
        )

        individual_failure_count = utilities.convert_failures_to_failure_count(
            scan_result.failures
        )

        log_data = (
            self.action_deps.logging.success(LogAction.scan)
            if scan_result.successful
            else self.action_deps.logging.failure(
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
            self.action_deps.echo.print(
                "Scan executed successfully and detected no issues!"
            )
        else:
            sys.exit(ExitCode.SCAN_ISSUES_DETECTED.value)

    def _check_secureli_hook_updates(self, folder_path: Path) -> install.VerifyResult:
        """
        Queries repositories referenced by pre-commit hooks to check
        if we have the latest revisions listed in the .pre-commit-config.yaml file
        :param folder_path: The folder path containing the .secureli/ folder
        """

        self.action_deps.echo.info("Checking for pre-commit hook updates...")
        pre_commit_config = self.hooks_scanner.pre_commit.get_pre_commit_config(
            folder_path
        )

        repos_to_update = self.hooks_scanner.pre_commit.check_for_hook_updates(
            pre_commit_config
        )

        if not repos_to_update:
            self.action_deps.echo.print("No hooks to update")
            return install.VerifyResult(outcome=install.VerifyOutcome.UP_TO_DATE)

        for repo, revs in repos_to_update.items():
            self.action_deps.echo.debug(
                f"Found update for {repo}: {revs.oldRev} -> {revs.newRev}"
            )
        self.action_deps.echo.warning(
            "You have out-of-date pre-commit hooks. Run `secureli update` to update them."
        )
        # Since we don't actually perform the updates here, return an outcome of UPDATE_CANCELLED
        return install.VerifyResult(outcome=install.VerifyOutcome.UPDATE_CANCELED)

    def _get_commited_files(self, scan_mode: ScanMode, folder_path: Path) -> list[Path]:
        """
        Attempts to build a list of commited files for use in language detection if
        the user is scanning staged files for an existing installation
        :param scan_mode: Determines which files are scanned in the repo (i.e. staged only or all)
        :returns: a list of Path objects for the commited files
        """
        config = self.get_secureli_config(reset=False)
        installed = bool(config.languages and config.version_installed)

        if not installed or scan_mode != ScanMode.STAGED_ONLY:
            return None
        try:
            committed_files = self.file_repo.list_staged_files(folder_path)
            return [Path(file) for file in committed_files]
        except:
            return None

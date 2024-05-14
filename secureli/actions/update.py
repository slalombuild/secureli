import re
from typing import List, Optional
from pathlib import Path
from secureli.modules.shared.abstractions.echo import EchoAbstraction
from secureli.modules.observability.observability_services.logging import LoggingService
from secureli.modules.core.core_services.updater import UpdaterService
from secureli.actions.action import Action, ActionDependencies
import secureli.modules.shared.models.repository as RepositoryModels

from rich.progress import Progress
from secureli.modules.shared.models.logging import LogAction


class UpdateAction(Action):
    def __init__(
        self,
        action_deps: ActionDependencies,
        updater: UpdaterService,
    ):
        super().__init__(action_deps)
        self.updater = updater

    def update_hooks(self, folder_path: Path, latest: Optional[bool] = False):
        """
        Installs the hooks defined in .pre-commit-config.yml.
        :param latest: Indicates whether you want to update to the latest versions
        of the installed hooks.
        :param folder_path: Indicates the git folder against which you run secureli
        :return: ExecuteResult, indicating success or failure.
        """
        with Progress(transient=True) as progress:
            if latest:
                self.action_deps.echo.print("Updating hooks to the latest version...")
                progress.add_task("Updating...", start=False, total=None)
                update_result = self.updater.update_hooks(folder_path)
                details = (
                    update_result.output
                    or "Unknown output while updating hooks to latest version"
                )
                progress.stop()
                self.action_deps.echo.print(details)
                if not update_result.successful:
                    self.action_deps.echo.print(details)
                    self.action_deps.logging.failure(LogAction.update, details)
                else:
                    self.action_deps.echo.print(
                        "Hooks successfully updated to latest version"
                    )
                    self.action_deps.logging.success(LogAction.update)
            else:
                self.action_deps.echo.print("Beginning update...")
                progress.add_task("Updating...", start=False, total=None)
                install_result = self.updater.update(folder_path)
                details = (
                    install_result.output or "Unknown output during hook installation"
                )
                progress.stop()
                self.action_deps.echo.print(details)
                if not install_result.successful:
                    self.action_deps.echo.print(details)
                    self.action_deps.logging.failure(LogAction.update, details)
                else:
                    self.action_deps.echo.print("Update executed successfully.")
                    self.action_deps.logging.success(LogAction.update)

    def _validate_regex(self, pattern: str) -> bool:
        """
        Checks if a given string is a valid Regex pattern, returns a boolean indicator
        param pattern: The string to be checked
        """
        try:
            re.compile(pattern)
            return True
        except:
            print(f'WARNING: invalid regex pattern detected: "{pattern}"\nExcluding pattern.\n')
            return False
        
    def _validate_pattern(self, pattern, patterns):
        """
        Checks the pattern is a valid Regex and is not already present in the patterns list
        param pattern: A string to be checked
        param patterns: A reference list to check for duplicate values
        """
        if pattern in patterns:
            print(f'WARNING: duplicate scan pattern detected: "{pattern}"\nExcluding pattern.\n')
            return False
        
        return self._validate_regex(pattern)

    def add_pattern(self, folder_path, patterns: List[str]):
        """
        Validates user provided scan patterns and stores them for future use
        :param folder_path: The folder secureli is operating in
        :param patterns: A user provided list of regex patterns to be saved
        """

        #Algorithm Notes:
        #for each pattern
        #   Check pattern is a valid regex
        #       if invalid, print warning and filter out pattern
        #   Check pattern is not present in custom_scan_patterns list
        #       if present, print warning and do not add duplicate
        #   Prevent repeated flags from being added twice
        #add new patterns to custom_scan_patterns list
        #save updated custom_scan_patterns list to secureli yaml file

        saved_patterns = []
        settings = self.action_deps.settings.load(folder_path)
        if settings.scan_patterns is not None:
            saved_patterns = settings.scan_patterns.custom_scan_patterns

        # Use a set comprehension to prevent flag duplicates
        new_patterns = { pattern for pattern in patterns if self._validate_pattern(pattern, saved_patterns)}
        saved_patterns.extend(new_patterns)

        if len(saved_patterns) > 0:
            settings.scan_patterns = RepositoryModels.CustomScanSettings(
                custom_scan_patterns=saved_patterns
            )
            self.action_deps.settings.save(settings)

        print("Current custom scan patterns:")
        print(*saved_patterns, sep="\n")


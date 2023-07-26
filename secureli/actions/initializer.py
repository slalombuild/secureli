from pathlib import Path

from secureli.actions.scan import ScanAction
from secureli.actions.action import Action, ActionDependencies
from secureli.services.logging import LoggingService, LogAction


class InitializerAction(Action):
    """The action for the SeCureLI `init` command, orchestrating services and outputs results"""

    def __init__(
        self,
        action_deps: ActionDependencies,
        logging: LoggingService,
    ):
        super().__init__(action_deps)
        self.logging = logging

    def initialize_repo(self, folder_path: Path, reset: bool, always_yes: bool):
        """
        Initializes SeCureLI for the specified folder path
        :param folder_path: The folder path to initialize the repo for
        :param reset: If true, disregard existing configuration and start fresh
        :param always_yes: Assume "Yes" to all prompts
        """

        # Will create a blank .secureli.yaml file if it does not exist
        settings = self.action_deps.settings.load()

        # Why are we saving settings? CLI should not be modifying them....just reading
        # With a templated example .secureli.yaml file, we won't be able to save
        # 1. Remove functionality that verifies pre-commit-config.yaml against generated template
        # 1. Remove functionality to automatically add ignores files and ignore hooks to .secureli.yaml/pre_commit.
        # 1. Remove settings.save()
        self.action_deps.settings.save(settings)

        verify_result = self.verify_install(folder_path, reset, always_yes)
        if verify_result.outcome in ScanAction.halting_outcomes:
            self.logging.failure(LogAction.init, verify_result.outcome)
        else:
            self.logging.success(LogAction.init)

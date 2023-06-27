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
        verify_result = self.verify_install(folder_path, reset, always_yes)
        if verify_result.outcome in ScanAction.halting_outcomes:
            self.logging.failure(LogAction.init, verify_result.outcome)
        else:
            self.logging.success(LogAction.init)

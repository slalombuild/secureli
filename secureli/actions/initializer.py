from pathlib import Path

from secureli.actions.scan import ScanAction
from secureli.actions.action import Action, ActionDependencies
from secureli.modules.observability.observability_services.logging import LoggingService
from secureli.modules.shared.models.install import VerifyResult
from secureli.modules.shared.models.logging import LogAction


class InitializerAction(Action):
    """The action for the seCureLI `init` command, orchestrating services and outputs results"""

    def __init__(
        self,
        action_deps: ActionDependencies,
        logging: LoggingService,
    ):
        super().__init__(action_deps)
        self.logging = logging

    def initialize_repo(
        self, folder_path: Path, reset: bool, always_yes: bool
    ) -> VerifyResult:
        """
        Initializes seCureLI for the specified folder path
        :param folder_path: The folder path to initialize the repo for
        :param reset: If true, disregard existing configuration and start fresh
        :param always_yes: Assume "Yes" to all prompts
        """
        verify_result = self.verify_install(folder_path, reset, always_yes, files=None)
        if verify_result.outcome in ScanAction.halting_outcomes:
            self.logging.failure(LogAction.init, verify_result.outcome)
        else:
            self.logging.success(LogAction.init)

        return verify_result

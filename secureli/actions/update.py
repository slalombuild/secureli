from typing import Optional
from pathlib import Path
from secureli.abstractions.echo import EchoAbstraction
from secureli.services.logging import LoggingService, LogAction
from secureli.services.updater import UpdaterService
from secureli.actions.action import Action, ActionDependencies


class UpdateAction(Action):
    def __init__(
        self,
        action_deps: ActionDependencies,
        echo: EchoAbstraction,
        logging: LoggingService,
        updater: UpdaterService,
    ):
        super().__init__(action_deps)
        self.echo = echo
        self.logging = logging
        self.updater = updater

    def update_hooks(self, folder_path: Path, latest: Optional[bool] = False):
        """
        Installs the hooks defined in .pre-commit-config.yml.
        :param latest: Indicates whether you want to update to the latest versions
        of the installed hooks.
        :param folder_path: Indicates the git folder against which you run secureli
        :return: ExecuteResult, indicating success or failure.
        """
        if latest:
            self.echo.print("Updating hooks to the latest version...")
            update_result = self.updater.update_hooks(folder_path)
            details = (
                update_result.output
                or "Unknown output while updating hooks to latest version"
            )
            self.echo.print(details)
            if not update_result.successful:
                self.echo.print(details)
                self.logging.failure(LogAction.update, details)
            else:
                self.echo.print("Hooks successfully updated to latest version")
                self.logging.success(LogAction.update)
        else:
            self.echo.print("Beginning update...")
            install_result = self.updater.update(folder_path)
            details = install_result.output or "Unknown output during hook installation"
            self.echo.print(details)
            if not install_result.successful:
                self.echo.print(details)
                self.logging.failure(LogAction.update, details)
            else:
                self.echo.print("Update executed successfully.")
                self.logging.success(LogAction.update)

from typing import Optional
from pathlib import Path
from secureli.modules.shared.abstractions.echo import EchoAbstraction
from secureli.modules.observability.observability_services.logging import LoggingService
from secureli.modules.core.core_services.updater import UpdaterService
from secureli.actions.action import Action, ActionDependencies

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

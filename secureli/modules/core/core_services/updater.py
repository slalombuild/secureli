from typing import Optional
from pathlib import Path

from secureli.modules.shared.abstractions.pre_commit import PreCommitAbstraction
from secureli.modules.shared.models.update import UpdateResult
from secureli.repositories.secureli_config import SecureliConfigRepository


class UpdaterService:
    """
    Handles update operations
    """

    def __init__(
        self,
        pre_commit: PreCommitAbstraction,
        config: SecureliConfigRepository,
    ):
        self.pre_commit = pre_commit
        self.config = config

    def update_hooks(
        self,
        folder_path: Path,
        bleeding_edge: bool = False,
        freeze: bool = False,
        repos: Optional[list] = None,
    ):
        """
        Updates the precommit hooks but executing precommit's autoupdate command.  Additional info at
        https://pre-commit.com/#pre-commit-autoupdate
        :param folder_path: Indicates the git folder against which you run secureli
        :param bleeding_edge: True if updating to the bleeding edge of the default branch instead of
        the latest tagged version (which is the default behavior)
        :param freeze: Set to True to store "frozen" hashes in rev instead of tag names.
        :param repos: Dectionary of repos to update. This is used to target specific repos instead of all repos.
        :return: ExecuteResult, indicating success or failure.
        """
        update_result = self.pre_commit.autoupdate_hooks(
            folder_path, bleeding_edge, freeze, repos
        )
        output = update_result.output

        if update_result.successful and not update_result.output:
            output = "No changes necessary.\n"

        if update_result.successful and update_result.output:
            prune_result = self.pre_commit.remove_unused_hooks(folder_path)
            output = output + "\nRemoving unused environments:\n" + prune_result.output

        return UpdateResult(successful=update_result.successful, output=output)

    def update(self, folder_path: Path = Path(".")):
        """
        Updates secureli with the latest local configuration.
        :param folder_path: Indicates the git folder against which you run secureli
        :return: ExecuteResult, indicating success or failure.
        """
        update_message = "Updating pre-commit hooks...\n"
        output = update_message

        hook_install_result = self.pre_commit.update(folder_path)
        output += hook_install_result.output

        if hook_install_result.successful and output == update_message:
            output += "No changes necessary.\n"

        if hook_install_result.successful and hook_install_result.output:
            prune_result = self.pre_commit.remove_unused_hooks(folder_path)
            output += "\nRemoving unused environments:\n" + prune_result.output

        return UpdateResult(successful=hook_install_result.successful, output=output)

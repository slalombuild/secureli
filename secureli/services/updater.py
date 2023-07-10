from typing import Optional

import pydantic

from secureli.abstractions.pre_commit import PreCommitAbstraction
from secureli.repositories.secureli_config import SecureliConfigRepository


class UpdateResult(pydantic.BaseModel):
    """
    The results of calling scan_repo
    """

    successful: bool
    output: Optional[str] = None


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
        bleeding_edge: bool = False,
        freeze: bool = False,
        repos: Optional[list] = None,
    ):
        """
        Updates the precommit hooks but executing precommit's autoupdate command.  Additional info at
        https://pre-commit.com/#pre-commit-autoupdate
        :param bleeding edge: True if updating to the bleeding edge of the default branch instead of
        the latest tagged version (which is the default behavior)
        :param freeze: Set to True to store "frozen" hashes in rev instead of tag names.
        :param repos: Dectionary of repos to update. This is used to target specific repos instead of all repos.
        :return: ExecuteResult, indicating success or failure.
        """
        update_result = self.pre_commit.autoupdate_hooks(bleeding_edge, freeze, repos)
        output = update_result.output

        if update_result.successful and not output:
            output = "No changes necessary.\n"

        if update_result.successful and update_result.output:
            prune_result = self.pre_commit.remove_unused_hooks()
            output = output + "\nRemoving unused environments:\n" + prune_result.output

        return UpdateResult(successful=update_result.successful, output=output)

    def update(self):
        """
        Updates secureli with the latest local configuration.
        :return: ExecuteResult, indicating success or failure.
        """
        secureli_config = self.config.load()
        output = "Updating .pre-commit-config.yaml...\n"
        install_result = self.pre_commit.install(language=secureli_config.languages[0])
        if not install_result.successful:
            output += "Failed to update .pre-commit-config.yaml prior to hook install\n"
            return UpdateResult(successful=install_result.successful, output=output)

        hook_install_result = self.pre_commit.update()
        output += hook_install_result.output

        if (
            hook_install_result.successful
            and output == "Updating .pre-commit-config.yaml...\n"
        ):
            output += "No changes necessary.\n"

        if hook_install_result.successful and hook_install_result.output:
            prune_result = self.pre_commit.remove_unused_hooks()
            output += "\nRemoving unused environments:\n" + prune_result.output

        return UpdateResult(successful=hook_install_result.successful, output=output)

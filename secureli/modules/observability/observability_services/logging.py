from pathlib import Path
from typing import Optional

import secureli.modules.shared.models.logging as LoggingModels
import secureli.repositories.secureli_config as SecureliConfig

from secureli.modules.language_analyzer import language_support
from secureli.repositories.secureli_config import SecureliConfigRepository
from secureli.modules.shared import utilities


class LoggingService:
    """Enables capturing secureli KPI log entries to a local file for future upload"""

    def __init__(
        self,
        language_support: language_support.LanguageSupportService,
        secureli_config: SecureliConfigRepository,
    ):
        self.language_support = language_support
        self.secureli_config = secureli_config

    def success(self, action: LoggingModels.LogAction) -> LoggingModels.LogEntry:
        """
        Capture that a successful conclusion has been reached for an action
        :param action: The action that succeeded
        """
        secureli_config = self.secureli_config.load()
        hook_config = (
            self.language_support.get_configuration(secureli_config.languages)
            if secureli_config.languages
            else None
        )
        log_entry = LoggingModels.LogEntry(
            status=LoggingModels.LogStatus.success,
            action=action,
            hook_config=hook_config,
            languages=secureli_config.languages if secureli_config.languages else None,
        )
        self._log(log_entry)

        return log_entry

    def failure(
        self,
        action: LoggingModels.LogAction,
        details: str,
        total_failure_count: Optional[int] = None,
        individual_failure_count: Optional[object] = None,
    ) -> LoggingModels.LogEntry:
        """
        Capture a failure against an action, with details
        :param action: The action that failed
        :param details: Details about the failure
        :param total_failure_count: The total failure count
        :param individual_failure_count: The individual failure count
        """
        secureli_config = self.secureli_config.load()
        hook_config = (
            None
            if not secureli_config.languages
            else self.language_support.get_configuration(secureli_config.languages)
        )
        log_entry = LoggingModels.LogEntry(
            status=LoggingModels.LogStatus.failure,
            action=action,
            failure=LoggingModels.LogFailure(
                details=details,
            ),
            total_failure_count=total_failure_count,
            failure_count_details=individual_failure_count,
            hook_config=hook_config,
            languages=secureli_config.languages if secureli_config.languages else None,
        )
        self._log(log_entry)

        return log_entry

    def _log(self, log_entry: LoggingModels.LogEntry):
        """Commit a log entry to the branch log file"""
        log_folder_path = Path(SecureliConfig.FOLDER_PATH / ".secureli/logs")
        path_to_log = log_folder_path / f"{utilities.current_branch_name()}"

        # Do not simply mkdir the log folder path, in case the branch name contains
        # additional folder structure, like `bugfix/` or `feature/`
        path_to_log.parent.mkdir(parents=True, exist_ok=True)
        with open(path_to_log, "a") as f:
            f.writelines([log_entry.json(exclude_none=True) + "\n"])

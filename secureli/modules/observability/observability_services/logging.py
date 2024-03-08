import platform
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Optional
from uuid import uuid4

import pydantic
from secureli.modules.shared.models.config import HookConfiguration
from secureli.modules.shared.models.logging import LogAction

import secureli.repositories.secureli_config as SecureliConfig
from secureli.modules.language_analyzer.language_analyzer_services import (
    language_support,
)
from secureli.repositories.secureli_config import SecureliConfigRepository
from secureli.modules.shared.utilities import git_meta
from secureli.modules.shared.utilities.secureli_meta import secureli_version


def generate_unique_id() -> str:
    """
    A unique identifier representing the log entry, including various
    bits specific to the user and environment
    """
    origin_email_branch = f"{git_meta.origin_url()}|{git_meta.git_user_email()}|{git_meta.current_branch_name()}"
    return f"{uuid4()}|{origin_email_branch}"


class LogStatus(str, Enum):
    """Whether the entry represents a successful or failing entry"""

    success = "SUCCESS"
    failure = "FAILURE"


class LogFailure(pydantic.BaseModel):
    """An extendable structure for log failures"""

    details: str


class LogEntry(pydantic.BaseModel):
    """A distinct entry in the log captured following actions like scan and init"""

    id: str = generate_unique_id()
    timestamp: datetime = datetime.utcnow()
    username: str = git_meta.git_user_email()
    machineid: str = platform.uname().node
    secureli_version: str = secureli_version()
    languages: Optional[list[str]]
    status: LogStatus
    action: LogAction
    hook_config: Optional[HookConfiguration]
    failure: Optional[LogFailure] = None
    total_failure_count: Optional[int]
    failure_count_details: Optional[object]


class LoggingService:
    """Enables capturing secureli KPI log entries to a local file for future upload"""

    def __init__(
        self,
        language_support: language_support.LanguageSupportService,
        secureli_config: SecureliConfigRepository,
    ):
        self.language_support = language_support
        self.secureli_config = secureli_config

    def success(self, action: LogAction) -> LogEntry:
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
        log_entry = LogEntry(
            status=LogStatus.success,
            action=action,
            hook_config=hook_config,
            languages=secureli_config.languages if secureli_config.languages else None,
        )
        self._log(log_entry)

        return log_entry

    def failure(
        self,
        action: LogAction,
        details: str,
        total_failure_count: Optional[int] = None,
        individual_failure_count: Optional[object] = None,
    ) -> LogEntry:
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
        log_entry = LogEntry(
            status=LogStatus.failure,
            action=action,
            failure=LogFailure(
                details=details,
            ),
            total_failure_count=total_failure_count,
            failure_count_details=individual_failure_count,
            hook_config=hook_config,
            languages=secureli_config.languages if secureli_config.languages else None,
        )
        self._log(log_entry)

        return log_entry

    def _log(self, log_entry: LogEntry):
        """Commit a log entry to the branch log file"""
        log_folder_path = Path(SecureliConfig.FOLDER_PATH / ".secureli/logs")
        path_to_log = log_folder_path / f"{git_meta.current_branch_name()}"

        # Do not simply mkdir the log folder path, in case the branch name contains
        # additional folder structure, like `bugfix/` or `feature/`
        path_to_log.parent.mkdir(parents=True, exist_ok=True)
        with open(path_to_log, "a") as f:
            f.writelines([log_entry.json(exclude_none=True) + "\n"])

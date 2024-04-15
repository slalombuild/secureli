from datetime import datetime
from enum import Enum
from typing import Optional

import platform
import pydantic

from secureli.modules.shared.models.config import HookConfiguration
from secureli.modules.shared import utilities


class LogAction(str, Enum):
    """Which action the log entry is associated with"""

    scan = "SCAN"
    init = "INIT"
    build = "_BUILD"
    update = "UPDATE"
    publish = "PUBLISH"  # "PUBLISH" does not correspond to a CLI action/subcommand


class LogStatus(str, Enum):
    """Whether the entry represents a successful or failing entry"""

    success = "SUCCESS"
    failure = "FAILURE"


class LogFailure(pydantic.BaseModel):
    """An extendable structure for log failures"""

    details: str


class LogEntry(pydantic.BaseModel):
    """A distinct entry in the log captured following actions like scan and init"""

    id: str = utilities.generate_unique_id()
    timestamp: datetime = datetime.utcnow()
    username: str = utilities.git_user_email()
    machineid: str = platform.uname().node
    secureli_version: str = utilities.secureli_version()
    languages: Optional[list[str]]
    status: LogStatus
    action: LogAction
    hook_config: Optional[HookConfiguration]
    failure: Optional[LogFailure] = None
    total_failure_count: Optional[int]
    failure_count_details: Optional[object]

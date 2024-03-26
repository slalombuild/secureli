from enum import Enum


class LogAction(str, Enum):
    """Which action the log entry is associated with"""

    scan = "SCAN"
    init = "INIT"
    build = "_BUILD"
    update = "UPDATE"
    publish = "PUBLISH"  # "PUBLISH" does not correspond to a CLI action/subcommand

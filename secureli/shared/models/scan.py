from enum import Enum

import pydantic


class ScanMode(str, Enum):
    """
    Which scan mode to run as when we perform scanning.
    """

    STAGED_ONLY = "staged-only"
    ALL_FILES = "all-files"


class ScanFailure(pydantic.BaseModel):
    """
    Represents the details of a failed rule from a scan
    """

    repo: str
    id: str
    file: str

from enum import Enum
from typing import Optional

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


class ScanOutput(pydantic.BaseModel):
    """
    Represents the parsed output from a scan
    """

    failures: list[ScanFailure]


class ScanResult(pydantic.BaseModel):
    """
    The results of calling scan_repo
    """

    successful: bool
    output: Optional[str] = None
    failures: list[ScanFailure]


class OutputParseErrors(str, Enum):
    """
    Possible errors when parsing scan output
    """

    REPO_NOT_FOUND = "repo-not-found"

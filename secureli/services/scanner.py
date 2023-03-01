from enum import Enum
from typing import Optional

import pydantic

from secureli.abstractions.pre_commit import PreCommitAbstraction


class ScanMode(str, Enum):
    """
    Which scan mode to run as when we perform scanning.
    """

    STAGED_ONLY = "staged-only"
    ALL_FILES = "all-files"


class ScanResult(pydantic.BaseModel):
    """
    The results of calling scan_repo
    """

    successful: bool
    output: Optional[str] = None


class ScannerService:
    """
    Scans the repo according to the repo's SeCureLI config
    """

    def __init__(self, pre_commit: PreCommitAbstraction):
        self.pre_commit = pre_commit

    def scan_repo(
        self, scan_mode: ScanMode, specific_test: Optional[str] = None
    ) -> ScanResult:
        """
        Scans the repo according to the repo's SeCureLI config
        :param scan_mode: Whether to scan the staged files (i.e., the files about to be
        committed) or the entire repository
        :param specific_test: If specified, limits the pre-commit execution to a single hook.
        If None, run all hooks.
        :return: A ScanResult object containing whether we succeeded and any error
        """
        all_files = True if scan_mode == ScanMode.ALL_FILES else False
        execute_result = self.pre_commit.execute_hooks(all_files, hook_id=specific_test)
        return ScanResult(
            successful=execute_result.successful, output=execute_result.output
        )

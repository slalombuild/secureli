from enum import Enum
from typing import Optional

import pydantic
import re

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


class Failure(pydantic.BaseModel):
    """
    Represents the details of a failed rule from a scan
    """

    id: str
    file: str


class ScanOuput(pydantic.BaseModel):
    """
    Represents the parsed output from a scan
    """

    failures: list[Failure]


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
        parsed_output = self._parse_scan_ouput(output=execute_result.output)

        for failure in parsed_output.failures:
            print("{} hook failed on file {}".format(failure.id, failure.file))

        return ScanResult(
            successful=execute_result.successful, output=execute_result.output
        )

    def _parse_scan_ouput(self, output: str = "") -> ScanOuput:
        """
        Parses the output from a scan and returns a list of Failure objects representing any
        hook rule failures during a scan.
        :param output: Raw output from a scan.
        :return: ScanOuput object representing a list of hook rule Failure objects.
        """
        failures = []
        failure_indexes = []

        output_by_line = output.split("\n")
        for index, line in enumerate(output_by_line):
            if line.find("Failed") != -1:
                failure_indexes.append(index)

        for failure_index in failure_indexes:
            id_with_encoding = output_by_line[failure_index + 1].split(": ")[1]
            id = self._remove_ansi_from_string(id_with_encoding)
            failure_output_list = self._get_single_failure_output(
                failure_start=failure_index, output_by_line=output_by_line
            )
            files = self._find_file_names(failure_output_list=failure_output_list)

            for file in files:
                failures.append(Failure(id=id, file=file))

        return ScanOuput(failures=failures)

    def _get_single_failure_output(
        self, failure_start: int, output_by_line: list[str]
    ) -> list[str]:
        failure_lines = []

        for index in range(failure_start + 1, len(output_by_line)):
            line = output_by_line[index]

            if line.find(".....") == -1:  # Look for line break
                failure_lines.append(line)
            else:
                break

        return failure_lines

    def _find_file_names(self, failure_output_list: list[str]) -> str:
        """
        Finds the file name for a hook rule failure
        :param failure_index: The index of the initial failure in failure_output_list
        :param output_by_line: List containing the scan output delimited by newlines
        :return: Returns the file name that caused the failure.
        """
        # regexp = re.compile(r"(\S*?\.\S*)")
        regexp = re.compile(r"^(?!http:|https)[a-z0-9-/]+\.+[a-z][^:\s]*")
        file_names = []
        for line in failure_output_list:
            words = line.split()
            for word in words:
                file_name = regexp.match(word)

                if file_name:
                    file_names.append(file_name.group(0))

        return file_names

    def _remove_ansi_from_string(self, string: str) -> str:
        """
        Removes ANSI encoding from a string.
        :param string: A string that needs to be processed
        :return: A string that has had its ANSI encoding removed
        """
        ansi_regexp = r"/(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]/"
        clean_string = re.sub(ansi_regexp, "", string)

        return clean_string

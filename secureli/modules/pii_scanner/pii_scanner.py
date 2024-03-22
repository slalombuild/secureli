from secureli.modules.shared.consts.pii import (
    DISABLE_PII_MARKER,
    Format,
    IGNORED_EXTENSIONS,
    PII_CHECK,
    RESULT_FORMAT,
    SECURELI_GITHUB,
)
import os
import re
from typing import Optional
from pathlib import Path
import pydantic

import secureli.modules.shared.models.scan as scan
from secureli.modules.shared.abstractions.echo import EchoAbstraction
from secureli.repositories.repo_files import RepoFilesRepository


class PiiResult(pydantic.BaseModel):
    """
    An individual result of potential PII found
    """

    line_num: int
    pii_key: str


class PiiScannerService:
    """
    Scans the repo for potential PII
    """

    def __init__(
        self,
        repo_files: RepoFilesRepository,
        echo: EchoAbstraction,
    ):
        self.repo_files = repo_files
        self.echo = echo

    def scan_repo(
        self,
        folder_path: Path,
        scan_mode: scan.ScanMode,
        files: Optional[list[str]] = None,
    ) -> scan.ScanResult:
        """
        Scans the repo for potential PII
        :param folder_path: The folder path to initialize the repo for
        :param scan_mode: Whether to scan the staged files (i.e., the files about to be
        committed) or the entire repository
        :param files: A specified list of files to scan
        :return: A ScanResult object with details of whether the scan succeeded and, if not, details of the failures
        """

        file_paths = self._get_files_list(
            folder_path=folder_path, scan_mode=scan_mode, files=files
        )
        current_line_num = 0
        pii_found: dict[str, list[PiiResult]] = {}
        pii_found_files = set()

        for file_path in file_paths:
            file_name = str(file_path)
            try:
                with open(file_path) as file:
                    for line in file:
                        current_line_num += 1
                        for pii_key, pii_regex in PII_CHECK.items():
                            if (
                                re.search(pii_regex, line.lower())
                                and not DISABLE_PII_MARKER in line
                            ):
                                if not file_name in pii_found:
                                    pii_found[file_name] = []
                                pii_found[file_name].append(
                                    {
                                        "line_num": current_line_num,
                                        "pii_key": pii_key,
                                    }
                                )
                                pii_found_files.add(file_name)
                current_line_num = 0

            except Exception as e:
                self.echo.print(f"Error PII scanning {file_name}: {e}")
        scan_failures = self._generate_scan_failures(pii_found_files)
        output = self._generate_scan_output(pii_found, not pii_found)

        return scan.ScanResult(
            successful=not pii_found,
            output=output,
            failures=scan_failures,
        )

    def _file_extension_excluded(self, filename) -> bool:
        _, file_extension = os.path.splitext(filename)
        if file_extension in IGNORED_EXTENSIONS:
            return True

        return False

    def _get_files_list(
        self,
        folder_path: Path,
        scan_mode: scan.ScanMode,
        files: Optional[list[str]] = None,
    ) -> list[Path]:
        """
        Gets the list of files to scan based on ScanMode and, if applicable, files provided in arguments
        Note: Files cannot be specified for the `all-files` ScanMode. Also, if a provided file is not staged,
        it will not be scanned
        :param folder_path: The folder path to initialize the repo for
        :param scan_mode: Whether to scan the staged files (i.e., the files about to be
        committed) or the entire repository
        :param files: A specified list of files to scan
        :return: List of file names to be scanned
        """
        file_paths: list[Path] = []

        if scan_mode == scan.ScanMode.STAGED_ONLY:
            file_paths = self.repo_files.list_staged_files(folder_path)
            if files:
                file_paths = list(filter(lambda file: file in file_paths, files))

        if scan_mode == scan.ScanMode.ALL_FILES:
            file_paths = self.repo_files.list_repo_files(folder_path)

        return list(
            filter(lambda file: not self._file_extension_excluded(file), file_paths)
        )

    def _generate_scan_failures(
        self, pii_found_files: set[str]
    ) -> list[scan.ScanFailure]:
        """
        Generates a list of ScanFailures for each file in which potential PII was found
        :param pii_found_files: The set of files in which potential PII was found
        :return: List of ScanFailures
        """
        failures = []

        for pii_found_file in pii_found_files:
            failures.append(
                scan.ScanFailure(
                    id="pii_scan", file=pii_found_file, repo=SECURELI_GITHUB
                )
            )
        return failures

    def _generate_initial_output(self, success: bool) -> str:
        """
        Generates the initial output of the PII scan, indicating whether the scan passed or failed
        :param success: Whether the scan passed
        :return: A string that will be used at the beginning of the output result
        """
        CHECK_STR = "check for PII"
        MAX_RESULT_LENGTH = (
            82  # this aims to align with the results output by pre-commit hooks
        )

        result = (
            self._format_string("Passed", [Format.GREEN_BG]) + " "
            if success
            else self._format_string("Failed", [Format.RED_BG]) + "\n"
        )
        length_of_dots = MAX_RESULT_LENGTH - len(CHECK_STR) - len(result)
        final_msg = (
            "\n"
            + self._format_string(
                "Potential PII found!", [Format.BOLD_WEIGHT, Format.RED_TXT]
            )
            if not success
            else ""
        )
        output = f"{CHECK_STR}{'.' * length_of_dots}{result}{final_msg}"

        return output

    def _generate_scan_output(
        self, pii_found: dict[str, list[PiiResult]], success: bool
    ) -> str:
        """
        Generates the scan output of the PII scan, listing all the areas where potential PII was found
        :param pii_found: The breakdown of what potential PII was found, and where
        :param success: Whether the scan passed
        :return: The final output result
        """
        output = self._generate_initial_output(success)
        for file, results in pii_found.items():
            output = (
                output
                + "\n"
                + self._format_string(
                    f"File: {file}", [Format.BOLD_WEIGHT, Format.PURPLE_TXT]
                )
            )
            for result in results:
                output = output + f"\n  Line {result['line_num']}: {result['pii_key']}"
        return output + "\n"

    def _format_string(self, str: str, formats: list[Format]) -> str:
        """
        Applies formatting to a string
        :param str: The string to format
        :param formats: The formatting to apply to the string
        :return: The formatted string
        """

        start = "".join(f"{RESULT_FORMAT[format]}" for format in formats)
        end = f"{RESULT_FORMAT[Format.DEFAULT]}{RESULT_FORMAT[Format.REG_WEIGHT]}"

        return f"{start}{str}{end}"

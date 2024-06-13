from secureli.modules.shared.consts.pii import (
    Format,
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
from secureli.modules.shared.abstractions.version_control_repo import (
    VersionControlRepoAbstraction,
)


class CustomRegexScanResult(pydantic.BaseModel):
    """
    An individual result of potential custom RegEx found
    """

    line_num: int
    regex_pattern: str


class CustomRegexScannerService:
    """
    Scans the repo for potential custom RegEx
    """

    def __init__(
        self,
        repo_files: VersionControlRepoAbstraction,
        echo: EchoAbstraction,
    ):
        self.repo_files = repo_files
        self.echo = echo

    def scan_repo(
        self,
        folder_path: Path,
        scan_mode: scan.ScanMode,
        custom_regex_patterns: list[str],
        files: Optional[list[str]] = None,
    ) -> scan.ScanResult:
        """
        Scans the repo for potential custom RegEx
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
        custom_regex_found: dict[str, list[CustomRegexScanResult]] = {}
        custom_regex_found_files = set()

        for file_path in file_paths:
            file_name = str(file_path)
            try:
                with open(file_path) as file:
                    for line in file:
                        current_line_num += 1
                        for custom_regex in custom_regex_patterns:
                            if re.search(custom_regex, line):
                                if not file_name in custom_regex_found:
                                    custom_regex_found[file_name] = []
                                custom_regex_found[file_name].append(
                                    {
                                        "line_num": current_line_num,
                                        "regex_pattern": custom_regex,
                                    }
                                )
                                custom_regex_found_files.add(file_name)
                current_line_num = 0

            except Exception as e:
                self.echo.print(f"Error scanning for custom RegEx {file_name}: {e}")
        scan_failures = self._generate_scan_failures(custom_regex_found_files)
        output = self._generate_scan_output(custom_regex_found, not custom_regex_found)

        return scan.ScanResult(
            successful=not custom_regex_found,
            output=output,
            failures=scan_failures,
        )

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
            filter(
                lambda file: file != ".secureli.yaml", file_paths
            )  # must exclude the .secureli.yaml file since it stores the regex patterns that are being checked
        )

    def _generate_scan_failures(
        self, custom_regex_found_files: set[str]
    ) -> list[scan.ScanFailure]:
        """
        Generates a list of ScanFailures for each file in which custom RegEx was found
        :param custom_regex_found_files: The set of files in which custom RegEx was found
        :return: List of ScanFailures
        """
        failures = []

        for file in custom_regex_found_files:
            failures.append(
                scan.ScanFailure(
                    id="custom_regex_scan", file=file, repo=SECURELI_GITHUB
                )
            )
        return failures

    def _generate_initial_output(self, success: bool) -> str:
        """
        Generates the initial output of the custom RegEx scan, indicating whether the scan passed or failed
        :param success: Whether the scan passed
        :return: A string that will be used at the beginning of the output result
        """
        CHECK_STR = "check for custom RegEx"
        MAX_RESULT_LENGTH = (
            93  # this aims to align with the results output by pre-commit hooks
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
                "Custom RegEx found!", [Format.BOLD_WEIGHT, Format.RED_TXT]
            )
            if not success
            else ""
        )
        output = f"{CHECK_STR}{'.' * length_of_dots}{result}{final_msg}"

        return output

    def _generate_scan_output(
        self, custom_regex_found: dict[str, list[CustomRegexScanResult]], success: bool
    ) -> str:
        """
        Generates the scan output of the PII scan, listing all the areas where potential PII was found
        :param custom_regex_found: The breakdown of what custom RegEx was found, and where
        :param success: Whether the scan passed
        :return: The final output result
        """
        output = self._generate_initial_output(success)
        for file, results in custom_regex_found.items():
            output = (
                output
                + "\n"
                + self._format_string(
                    f"File: {file}", [Format.BOLD_WEIGHT, Format.PURPLE_TXT]
                )
            )
            for result in results:
                print(result)
                output = (
                    output
                    + f"\n  Line {result['line_num']} | Pattern Matched: {result['regex_pattern']}"
                )
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

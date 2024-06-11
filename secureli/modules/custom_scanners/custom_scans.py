from enum import Enum
from typing import Optional
from pathlib import Path

from secureli.modules.custom_scanners.custom_regex_scanner.custom_regex_scanner import (
    CustomRegexScannerService,
)
from secureli.modules.custom_scanners.pii_scanner.pii_scanner import PiiScannerService
from secureli.modules.shared import utilities
import secureli.modules.shared.models.scan as scan


class CustomScanId(str, Enum):
    """
    Scan ids of custom scans
    """

    PII = "check-pii"
    CUSTOM_REGEX = "check-regex"


class CustomScannersService:
    """
    This service orchestrates running custom scans. A custom scan is a
    scan that is not a precommit hook scan, i.e. PII and custom regex scans.
    """

    def __init__(
        self,
        pii_scanner: PiiScannerService,
        custom_regex_scanner: CustomRegexScannerService,
    ):
        self.pii_scanner = pii_scanner
        self.custom_regex_scanner = custom_regex_scanner

    def scan_repo(
        self,
        folder_path: Path,
        scan_mode: scan.ScanMode,
        custom_scan_id: Optional[str] = None,
        files: Optional[str] = None,
    ) -> scan.ScanResult:
        # If no custom scan is specified, run all custom scans
        if custom_scan_id is None:
            pii_scan_result = self.pii_scanner.scan_repo(
                folder_path, scan_mode, files=files
            )
            regex_scan_result = self.custom_regex_scanner.scan_repo(
                folder_path=folder_path, scan_mode=scan_mode, files=files
            )
            custom_scan_results = utilities.merge_scan_results(
                [pii_scan_result, regex_scan_result]
            )
            return custom_scan_results

        # If the specified scan isn't known, do nothing
        if custom_scan_id not in CustomScanId.__members__.values():
            return None

        # Run the specified custom scan only
        scan_results = None
        if custom_scan_id == CustomScanId.PII:
            scan_results = self.pii_scanner.scan_repo(
                folder_path, scan_mode, files=files
            )
        elif custom_scan_id == CustomScanId.CUSTOM_REGEX:
            scan_results = self.custom_regex_scanner.scan_repo(
                folder_path=folder_path, scan_mode=scan_mode, files=files
            )

        return scan_results

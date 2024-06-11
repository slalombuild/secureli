import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock, Mock, patch
from pathlib import Path

from secureli.modules.custom_scanners.custom_regex_scanner.custom_regex_scanner import (
    CustomRegexScannerService,
)
from secureli.modules.custom_scanners.custom_scans import (
    CustomScanId,
    CustomScannersService,
)
from secureli.modules.shared.models import scan
from secureli.modules.shared.models.echo import Level
from secureli.modules.shared.models.scan import ScanMode
import secureli.modules.shared.models.repository as RepositoryModels
from secureli.repositories import repo_settings

test_folder_path = Path(".")


@pytest.fixture()
def mock_pii_scanner_service() -> MagicMock:
    mock_pii_scanner_service = MagicMock()
    mock_pii_scanner_service.scan_repo.return_value = []
    return mock_pii_scanner_service


@pytest.fixture()
def mock_custom_regex_scanner_service() -> MagicMock:
    mock_custom_regex_scanner_service = MagicMock()
    mock_custom_regex_scanner_service.scan_repo.return_value = []
    return mock_custom_regex_scanner_service


@pytest.fixture()
def custom_scanner_service(
    mock_pii_scanner_service: MagicMock,
    mock_custom_regex_scanner_service: MagicMock,
) -> CustomRegexScannerService:
    return CustomScannersService(
        mock_pii_scanner_service, mock_custom_regex_scanner_service
    )


def test_that_pii_scan_executes(
    custom_scanner_service: CustomScannersService,
    mock_pii_scanner_service: MagicMock,
):

    custom_scanner_service.scan_repo(
        test_folder_path,
        ScanMode.STAGED_ONLY,
        CustomScanId.PII,
    )

    mock_pii_scanner_service.scan_repo.assert_called_once()


def test_that_custom_regex_scan_executes(
    custom_scanner_service: CustomScannersService,
    mock_custom_regex_scanner_service: MagicMock,
):

    custom_scanner_service.scan_repo(
        test_folder_path,
        ScanMode.ALL_FILES,
        CustomScanId.CUSTOM_REGEX,
    )

    mock_custom_regex_scanner_service.scan_repo.assert_called_once()


def test_that_all_custom_scans_execute_when_no_id_given(
    custom_scanner_service: CustomScannersService,
    mock_pii_scanner_service: MagicMock,
    mock_custom_regex_scanner_service: MagicMock,
):

    custom_scanner_service.scan_repo(test_folder_path, ScanMode.STAGED_ONLY)

    mock_pii_scanner_service.scan_repo.assert_called_once()
    mock_custom_regex_scanner_service.scan_repo.assert_called_once()


def test_that_no_custom_scans_run_when_unknown_id_provided(
    custom_scanner_service: CustomScannersService,
    mock_pii_scanner_service: MagicMock,
    mock_custom_regex_scanner_service: MagicMock,
):

    scan_results = custom_scanner_service.scan_repo(
        test_folder_path, ScanMode.STAGED_ONLY, "non-existent-scan-id"
    )

    mock_pii_scanner_service.scan_repo.assert_not_called()
    mock_custom_regex_scanner_service.scan_repo.assert_not_called()
    assert scan_results == None

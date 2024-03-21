import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock
from pathlib import Path
from secureli.modules.pii_scanner.pii_scanner import PiiScannerService
from secureli.modules.shared.models.scan import ScanMode


test_folder_path = Path(".")


@pytest.fixture()
def mock_repo_files_repository() -> MagicMock:
    mock_repo_files_repository = MagicMock()
    mock_repo_files_repository.list_staged_files.return_value = ["fake_file_path"]
    mock_repo_files_repository.list_repo_files.return_value = ["fake_file_path"]
    return mock_repo_files_repository


@pytest.fixture()
def mock_open_fn(mocker: MockerFixture) -> MagicMock:
    # TODO435: mock PII data below
    mock_open = mocker.mock_open(
        read_data="""
        fake_email='pantsATpants.com'
        fake_phone='phone-num-here'
      """
    )
    return mocker.patch("builtins.open", mock_open)


@pytest.fixture()
def pii_scanner_service(mock_repo_files_repository: MagicMock) -> PiiScannerService:
    return PiiScannerService(mock_repo_files_repository)


def test_that_pii_scanner_service_finds_potential_pii(
    pii_scanner_service: PiiScannerService,
    mock_repo_files_repository: MagicMock,
    mock_open_fn: MagicMock,
):
    scan_result = pii_scanner_service.scan_repo(test_folder_path, ScanMode.STAGED_ONLY)

    mock_repo_files_repository.list_staged_files.assert_called_once()
    # TODO435: uncomment once dummy PII data available
    # assert scan_result.successful == False
    # assert len(scan_result.failures) == 1
    # assert "Email" in scan_result.output
    # assert "Phone number" in scan_result.output


def test_that_pii_scanner_service_scans_all_files_when_specified(
    pii_scanner_service: PiiScannerService,
    mock_repo_files_repository: MagicMock,
    mock_open_fn: MagicMock,
):
    pii_scanner_service.scan_repo(test_folder_path, ScanMode.ALL_FILES)

    mock_repo_files_repository.list_repo_files.assert_called_once()


def test_that_pii_scanner_service_ignores_excluded_file_extensions(
    pii_scanner_service: PiiScannerService,
    mock_repo_files_repository: MagicMock,
    mock_open_fn: MagicMock,
):
    mock_repo_files_repository.list_staged_files.return_value = ["fake_file_path.md"]

    scan_result = pii_scanner_service.scan_repo(test_folder_path, ScanMode.STAGED_ONLY)

    assert scan_result.successful == True


def test_that_pii_scanner_service_only_scans_specific_files_if_provided(
    pii_scanner_service: PiiScannerService,
    mock_repo_files_repository: MagicMock,
    mock_open_fn: MagicMock,
):
    specified_file = "fake_file_path"
    ignored_file = "not-the-file-we-want"
    mock_repo_files_repository.list_staged_files.return_value = [
        specified_file,
        ignored_file,
    ]
    scan_result = pii_scanner_service.scan_repo(
        test_folder_path, ScanMode.STAGED_ONLY, [specified_file]
    )

    # TODO435: uncomment once dummy PII data available
    # assert scan_result.successful == False
    # assert len(scan_result.failures) == 1
    # assert scan_result.failures[0].file == specified_file

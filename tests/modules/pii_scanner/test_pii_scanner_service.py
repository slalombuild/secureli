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
    mock_repo_files_repository.list_staged_files.return_value = [Path("fake_file_path")]
    mock_repo_files_repository.list_repo_files.return_value = [Path("fake_file_path")]
    return mock_repo_files_repository


@pytest.fixture()
def mock_open_fn(mocker: MockerFixture) -> MagicMock:
    mock_open = mocker.mock_open(
        read_data="fake_email='pantsATpants.com'"  # TODO: mock PII data here
    )
    return mocker.patch("builtins.open", mock_open)


@pytest.fixture()
def pii_scanner_service(mock_repo_files_repository: MagicMock) -> PiiScannerService:
    return PiiScannerService(mock_repo_files_repository)


def test_that_pii_scanner_service_finds_potential_pii(
    pii_scanner_service: PiiScannerService,
    mock_open_fn: MagicMock,
):
    scan_result = pii_scanner_service.scan_repo(test_folder_path, ScanMode.ALL_FILES)

    # assert not scan_result.successful # TODO: uncomment once dummy PII data available

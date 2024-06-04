import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock, Mock
import builtins
import contextlib, io
from pathlib import Path
from secureli.modules.pii_scanner.pii_scanner import PiiScannerService
from secureli.modules.shared.consts.pii import IGNORED_EXTENSIONS
from secureli.modules.shared.models.scan import ScanMode


test_folder_path = Path(".")


@pytest.fixture()
def mock_repo_files_repository() -> MagicMock:
    mock_repo_files_repository = MagicMock()
    mock_repo_files_repository.list_staged_files.return_value = ["fake_file_path"]
    mock_repo_files_repository.list_repo_files.return_value = ["fake_file_path"]
    return mock_repo_files_repository


@pytest.fixture()
def mock_echo() -> MagicMock:
    mock_echo = MagicMock()
    return mock_echo


@pytest.fixture()
def mock_open_fn(mocker: MockerFixture) -> MagicMock:
    # The below data wouldn't ACTUALLY count as PII, but using fake PII here would prevent this code
    # from being committed (as seCureLi scans itself before commit!)
    # Instead, we mock the regex search function to pretend we found a PII match so we can assert the
    # scanner's behavior
    mock_open = mocker.mock_open(
        read_data="""
        fake_email='pantsATpants.com'
        fake_phone='phone-num-here'
      """
    )
    return mocker.patch("builtins.open", mock_open)


# Include the below for any tests where you want PII to be "found"
@pytest.fixture()
def mock_re(mocker: MockerFixture) -> MagicMock:
    match_object = mocker.patch("re.Match", lambda *args: True)
    return mocker.patch("re.search", match_object)


@pytest.fixture()
def pii_scanner_service(
    mock_repo_files_repository: MagicMock, mock_echo: MagicMock
) -> PiiScannerService:
    return PiiScannerService(mock_repo_files_repository, mock_echo, ignored_extensions=IGNORED_EXTENSIONS)


def test_that_pii_scanner_service_finds_potential_pii(
    pii_scanner_service: PiiScannerService,
    mock_repo_files_repository: MagicMock,
    mock_open_fn: MagicMock,
    mock_re: MagicMock,
):
    scan_result = pii_scanner_service.scan_repo(test_folder_path, ScanMode.STAGED_ONLY)

    mock_repo_files_repository.list_staged_files.assert_called_once()

    assert scan_result.successful == False
    assert len(scan_result.failures) == 1
    assert "Email" in scan_result.output
    assert "Phone number" in scan_result.output


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
    mock_re: MagicMock,
):
    mock_repo_files_repository.list_staged_files.return_value = ["fake_file_path.md"]

    scan_result = pii_scanner_service.scan_repo(test_folder_path, ScanMode.STAGED_ONLY)

    assert scan_result.successful == True


def test_that_pii_scanner_service_only_scans_specific_files_if_provided(
    pii_scanner_service: PiiScannerService,
    mock_repo_files_repository: MagicMock,
    mock_open_fn: MagicMock,
    mock_re: MagicMock,
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

    assert scan_result.successful == False
    assert len(scan_result.failures) == 1
    assert scan_result.failures[0].file == specified_file


def test_that_pii_scanner_prints_when_exceptions_encountered(
    pii_scanner_service: PiiScannerService,
    mock_open_fn: MagicMock,
    mock_echo: MagicMock,
):
    mock_open_fn.side_effect = Exception("Oh no")
    pii_scanner_service.scan_repo(
        test_folder_path,
        ScanMode.STAGED_ONLY,
    )

    mock_echo.print.assert_called_once()
    assert "Error PII scanning" in mock_echo.print.call_args.args[0]

import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock, Mock
from pathlib import Path
from secureli.modules.custom_scanner.custom_scanner import CustomScannerService
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
def custom_regex_patterns() -> list[str]:
    return [
        "\w*testing data"  # any mock files containing "testing data" should fail scan
    ]


@pytest.fixture()
def mock_open_fn(mocker: MockerFixture) -> MagicMock:
    # The below data wouldn't ACTUALLY count as PII, but using fake PII here would prevent this code
    # from being committed (as seCureLi scans itself before commit!)
    # Instead, we mock the regex search function to pretend we found a PII match so we can assert the
    # scanner's behavior
    mock_open = mocker.mock_open(
        read_data="""
        This is some testing data that should be flagged by the
        custom regex pattern defined in the custom_regex_patterns fixture
      """
    )
    return mocker.patch("builtins.open", mock_open)


# Include the below for any tests where you want regex to be "found"
@pytest.fixture()
def mock_re(mocker: MockerFixture) -> MagicMock:
    match_object = mocker.patch("re.Match", lambda *args: True)
    return mocker.patch("re.search", match_object)


@pytest.fixture()
def custom_scanner_service(
    mock_repo_files_repository: MagicMock, mock_echo: MagicMock
) -> CustomScannerService:
    return CustomScannerService(mock_repo_files_repository, mock_echo)


def test_that_custom_scanner_service_finds_regex(
    custom_scanner_service: CustomScannerService,
    mock_repo_files_repository: MagicMock,
    custom_regex_patterns: list[str],
    mock_open_fn: MagicMock,
    mock_re: MagicMock,
):
    scan_result = custom_scanner_service.scan_repo(
        folder_path=test_folder_path,
        scan_mode=ScanMode.STAGED_ONLY,
        custom_regex_patterns=custom_regex_patterns,
    )

    mock_repo_files_repository.list_staged_files.assert_called_once()

    assert scan_result.successful == False
    assert len(scan_result.failures) == 1
    assert "Pattern Matched:" in scan_result.output


def test_that_custom_scanner_service_scans_all_files_when_specified(
    custom_scanner_service: CustomScannerService,
    mock_repo_files_repository: MagicMock,
    custom_regex_patterns: list[str],
    mock_open_fn: MagicMock,
):
    custom_scanner_service.scan_repo(
        folder_path=test_folder_path,
        scan_mode=ScanMode.ALL_FILES,
        custom_regex_patterns=custom_regex_patterns,
    )

    mock_repo_files_repository.list_repo_files.assert_called_once()


def test_that_custom_scanner_service_ignores_secureli_yaml(
    custom_scanner_service: CustomScannerService,
    mock_repo_files_repository: MagicMock,
    custom_regex_patterns: list[str],
    mock_open_fn: MagicMock,
    mock_re: MagicMock,
):
    mock_repo_files_repository.list_staged_files.return_value = [".secureli.yaml"]

    scan_result = custom_scanner_service.scan_repo(
        folder_path=test_folder_path,
        scan_mode=ScanMode.STAGED_ONLY,
        custom_regex_patterns=custom_regex_patterns,
    )

    assert scan_result.successful == True


def test_that_pii_scanner_service_only_scans_specific_files_if_provided(
    custom_scanner_service: CustomScannerService,
    mock_repo_files_repository: MagicMock,
    custom_regex_patterns: list[str],
    mock_open_fn: MagicMock,
    mock_re: MagicMock,
):
    specified_file = "fake_file_path"
    ignored_file = "not-the-file-we-want"
    mock_repo_files_repository.list_staged_files.return_value = [
        specified_file,
        ignored_file,
    ]
    scan_result = custom_scanner_service.scan_repo(
        folder_path=test_folder_path,
        scan_mode=ScanMode.STAGED_ONLY,
        files=[specified_file],
        custom_regex_patterns=custom_regex_patterns,
    )

    assert scan_result.successful == False
    assert len(scan_result.failures) == 1
    assert scan_result.failures[0].file == specified_file


def test_that_pii_scanner_prints_when_exceptions_encountered(
    custom_scanner_service: CustomScannerService,
    custom_regex_patterns: list[str],
    mock_open_fn: MagicMock,
    mock_echo: MagicMock,
):
    mock_open_fn.side_effect = Exception("Oh no")
    custom_scanner_service.scan_repo(
        folder_path=test_folder_path,
        scan_mode=ScanMode.STAGED_ONLY,
        custom_regex_patterns=custom_regex_patterns,
    )

    mock_echo.print.assert_called_once()
    assert "Error scanning for custom RegEx" in mock_echo.print.call_args.args[0]

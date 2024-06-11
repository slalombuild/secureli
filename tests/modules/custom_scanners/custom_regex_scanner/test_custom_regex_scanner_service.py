import pytest
from pytest_mock import MockerFixture
from unittest.mock import MagicMock, Mock, patch
from pathlib import Path

from secureli.modules.custom_scanners.custom_regex_scanner.custom_regex_scanner import (
    CustomRegexScannerService,
)
from secureli.modules.shared.models.echo import Level
from secureli.modules.shared.models.scan import ScanMode
import secureli.modules.shared.models.repository as RepositoryModels
from secureli.repositories import repo_settings

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
def mock_settings() -> MagicMock:
    mock_settings = MagicMock()
    return mock_settings


@pytest.fixture()
def mock_settings_no_scan_patterns(mock_settings_repository: MagicMock) -> MagicMock:
    mock_echo_settings = RepositoryModels.EchoSettings(level=Level.info)
    mock_settings_file = repo_settings.SecureliFile(echo=mock_echo_settings)
    mock_settings_file.scan_patterns = None
    mock_settings_repository.load.return_value = mock_settings_file

    return mock_settings_repository


@pytest.fixture()
def mock_custom_regex_patterns() -> list[str]:
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
def custom_regex_scanner_service(
    mock_repo_files_repository: MagicMock,
    mock_echo: MagicMock,
    mock_settings: MagicMock,
    mock_custom_regex_patterns: MagicMock,
) -> CustomRegexScannerService:
    regexService = CustomRegexScannerService(
        mock_repo_files_repository, mock_echo, mock_settings
    )
    regexService._get_custom_scan_patterns = MagicMock()
    regexService._get_custom_scan_patterns.return_value = mock_custom_regex_patterns
    return regexService


def test_that_custom_regex_scanner_service_finds_regex(
    custom_regex_scanner_service: CustomRegexScannerService,
    mock_repo_files_repository: MagicMock,
    mock_open_fn: MagicMock,
    mock_re: MagicMock,
):

    scan_result = custom_regex_scanner_service.scan_repo(
        folder_path=test_folder_path, scan_mode=ScanMode.STAGED_ONLY
    )

    mock_repo_files_repository.list_staged_files.assert_called_once()

    assert scan_result.successful == False
    assert len(scan_result.failures) == 1
    assert "Pattern Matched:" in scan_result.output


def test_that_custom_regex_scanner_service_scans_all_files_when_specified(
    custom_regex_scanner_service: CustomRegexScannerService,
    mock_repo_files_repository: MagicMock,
    mock_open_fn: MagicMock,
):
    custom_regex_scanner_service.scan_repo(
        folder_path=test_folder_path, scan_mode=ScanMode.ALL_FILES
    )

    mock_repo_files_repository.list_repo_files.assert_called_once()


def test_that_custom_regex_scanner_service_ignores_secureli_yaml(
    custom_regex_scanner_service: CustomRegexScannerService,
    mock_repo_files_repository: MagicMock,
    mock_open_fn: MagicMock,
    mock_re: MagicMock,
):
    mock_repo_files_repository.list_staged_files.return_value = [".secureli.yaml"]

    scan_result = custom_regex_scanner_service.scan_repo(
        folder_path=test_folder_path, scan_mode=ScanMode.STAGED_ONLY
    )

    assert scan_result.successful == True


def test_that_pii_scanner_service_only_scans_specific_files_if_provided(
    custom_regex_scanner_service: CustomRegexScannerService,
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
    scan_result = custom_regex_scanner_service.scan_repo(
        folder_path=test_folder_path,
        scan_mode=ScanMode.STAGED_ONLY,
        files=[specified_file],
    )

    assert scan_result.successful == False
    assert len(scan_result.failures) == 1
    assert scan_result.failures[0].file == specified_file


def test_that_pii_scanner_prints_when_exceptions_encountered(
    custom_regex_scanner_service: CustomRegexScannerService,
    mock_open_fn: MagicMock,
    mock_echo: MagicMock,
):
    mock_open_fn.side_effect = Exception("Oh no")
    custom_regex_scanner_service.scan_repo(
        folder_path=test_folder_path, scan_mode=ScanMode.STAGED_ONLY
    )

    mock_echo.print.assert_called_once()
    assert "Error scanning for custom RegEx" in mock_echo.print.call_args.args[0]


def test_coverage_that_get_regex_pattern_returns_custom_patterns(
    mock_repo_files_repository: MagicMock,
    mock_echo: MagicMock,
    mock_settings: MagicMock,
):
    custom_regex_scanner_service = CustomRegexScannerService(
        mock_repo_files_repository, mock_echo, mock_settings
    )

    custom_regex_scanner_service.scan_repo(
        folder_path=test_folder_path, scan_mode=ScanMode.STAGED_ONLY
    )


def test_coverage_that_get_regex_pattern_returns_no_custom_patterns(
    mock_repo_files_repository: MagicMock,
    mock_echo: MagicMock,
    mock_settings_no_scan_patterns,
):
    custom_regex_scanner_service = CustomRegexScannerService(
        mock_repo_files_repository, mock_echo, mock_settings_no_scan_patterns
    )

    custom_regex_scanner_service.scan_repo(
        folder_path=test_folder_path, scan_mode=ScanMode.STAGED_ONLY
    )

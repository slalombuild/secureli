from unittest.mock import MagicMock
from pathlib import Path
import pytest

from secureli.abstractions.pre_commit import ExecuteResult
from secureli.services.scanner import ScannerService, ScanMode, OutputParseErrors
from pytest_mock import MockerFixture

test_folder_path = Path("does-not-matter")


@pytest.fixture()
def mock_scan_output_no_failure():
    output = """
    check docstring is first.................................................Passed
    check that executables have shebangs.................(no files to check)Skipped

    All done! ✨ 🍰 ✨
    1 file reformatted.
    """
    return output


@pytest.fixture()
def mock_scan_output_single_failure():
    output = """
    check docstring is first.................................................Passed
    check that executables have shebangs.................(no files to check)Skipped
    python tests naming......................................................Passed
    trim trailing whitespace.................................................Failed
    - hook id: trailing-whitespace
    - exit code: 1
    - files were modified by this hook

    Fixing tests/services/test_scanner_service.py

    fix end of files.........................................................Passed
    check yaml...........................................(no files to check)Skipped

    All done! ✨ 🍰 ✨
    1 file reformatted.
    """
    return output


@pytest.fixture()
def mock_scan_output_double_failure():
    output = """
    check docstring is first.................................................Passed
    check that executables have shebangs.................(no files to check)Skipped
    python tests naming......................................................Passed
    trim trailing whitespace.................................................Failed
    - hook id: trailing-whitespace
    - exit code: 1
    - files were modified by this hook

    Fixing tests/services/test_scanner_service.py

    fix end of files.........................................................Passed
    check yaml...........................................(no files to check)Skipped
    black....................................................................Failed
    - hook id: black
    - files were modified by this hook

    reformatted tests/services/test_scanner_service.py

    All done! ✨ 🍰 ✨
    1 file reformatted.
    """
    return output


@pytest.fixture()
def mock_config_all_repos(mocker: MockerFixture) -> MagicMock:
    mock_data = r"""
    exclude: ^(?:.+/)?\.idea(?P<ps_d>/).*$
    repos:
    - hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      repo: https://github.com/pre-commit/pre-commit-hooks
      rev: v4.3.0
    - hooks:
      - id: black
      repo: https://github.com/psf/black
      rev: 22.10.0
    """
    mock_open = mocker.mock_open(read_data=mock_data)
    mocker.patch("builtins.open", mock_open)
    return mock_open


@pytest.fixture()
def mock_config_no_black(mocker: MockerFixture) -> MagicMock:
    mock_data = r"""
    exclude: ^(?:.+/)?\.idea(?P<ps_d>/).*$
    repos:
    - hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      repo: https://github.com/pre-commit/pre-commit-hooks
      rev: v4.3.0
    """
    mock_open = mocker.mock_open(read_data=mock_data)
    mocker.patch("builtins.open", mock_open)
    return mock_open


@pytest.fixture()
def scanner_service(mock_pre_commit: MagicMock) -> ScannerService:
    return ScannerService(mock_pre_commit)


def test_that_scanner_service_scans_repositories_with_pre_commit(
    scanner_service: ScannerService,
    mock_pre_commit: MagicMock,
):
    scan_result = scanner_service.scan_repo(test_folder_path, ScanMode.ALL_FILES)

    mock_pre_commit.execute_hooks.assert_called_once()
    assert scan_result.successful


def test_that_scanner_service_parses_failures(
    scanner_service: ScannerService,
    mock_pre_commit: MagicMock,
    mock_scan_output_single_failure: MagicMock,
    mock_config_all_repos: MagicMock,
):
    mock_pre_commit.execute_hooks.return_value = ExecuteResult(
        successful=True, output=mock_scan_output_single_failure
    )
    scan_result = scanner_service.scan_repo(test_folder_path, ScanMode.ALL_FILES)

    assert len(scan_result.failures) is 1


def test_that_scanner_service_parses_multiple_failures(
    scanner_service: ScannerService,
    mock_pre_commit: MagicMock,
    mock_scan_output_double_failure: MagicMock,
    mock_config_all_repos: MagicMock,
):
    mock_pre_commit.execute_hooks.return_value = ExecuteResult(
        successful=True, output=mock_scan_output_double_failure
    )
    scan_result = scanner_service.scan_repo(test_folder_path, ScanMode.ALL_FILES)

    assert len(scan_result.failures) is 2


def test_that_scanner_service_parses_when_no_failures(
    scanner_service: ScannerService,
    mock_pre_commit: MagicMock,
    mock_scan_output_no_failure: MagicMock,
    mock_config_all_repos: MagicMock,
):
    mock_pre_commit.execute_hooks.return_value = ExecuteResult(
        successful=True, output=mock_scan_output_no_failure
    )
    scan_result = scanner_service.scan_repo(test_folder_path, ScanMode.ALL_FILES)

    assert len(scan_result.failures) is 0


def test_that_scanner_service_handles_error_in_missing_repo(
    scanner_service: ScannerService,
    mock_pre_commit: MagicMock,
    mock_scan_output_double_failure: MagicMock,
    mock_config_no_black: MagicMock,
):
    mock_pre_commit.execute_hooks.return_value = ExecuteResult(
        successful=True, output=mock_scan_output_double_failure
    )
    scan_result = scanner_service.scan_repo(test_folder_path, ScanMode.ALL_FILES)

    assert scan_result.failures[1].repo == OutputParseErrors.REPO_NOT_FOUND

from unittest.mock import MagicMock

import pytest

from secureli.abstractions.pre_commit import ExecuteResult
from secureli.services.scanner import ScannerService, ScanMode


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
def scanner_service(mock_pre_commit: MagicMock) -> ScannerService:
    return ScannerService(mock_pre_commit)


# def test_that_scanner_service_scans_repositories_with_pre_commit(
#     scanner_service: ScannerService,
#     mock_pre_commit: MagicMock,
# ):
#     scan_result = scanner_service.scan_repo(ScanMode.ALL_FILES)

#     mock_pre_commit.execute_hooks.assert_called_once()
#     assert scan_result.successful


def test_that_scanner_service_parses_failures(
    scanner_service: ScannerService,
    mock_pre_commit: MagicMock,
    mock_scan_output_single_failure: MagicMock,
):
    mock_pre_commit.execute_hooks.return_value = ExecuteResult(
        successful=True, output=mock_scan_output_single_failure
    )
    scan_result = scanner_service.scan_repo(ScanMode.ALL_FILES)

    assert len(scan_result.failures) is 1

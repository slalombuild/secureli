from unittest.mock import MagicMock

import pytest

from secureli.abstractions.pre_commit import ExecuteResult
from secureli.services.scanner import ScannerService, ScanMode


@pytest.fixture()
def scanner_service(mock_pre_commit: MagicMock) -> ScannerService:
    return ScannerService(mock_pre_commit)


def test_that_scanner_service_scans_repositories_with_pre_commit(
    scanner_service: ScannerService,
    mock_pre_commit: MagicMock,
):
    scan_result = scanner_service.scan_repo(ScanMode.ALL_FILES)

    mock_pre_commit.execute_hooks.assert_called_once()
    assert scan_result.successful

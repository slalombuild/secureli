import pytest
from unittest.mock import MagicMock
from secureli.modules.pii_scanner.pii_scanner import PiiScannerService


@pytest.fixture()
def mock_repo_files_repository() -> MagicMock:
    mock_repo_files_repository = MagicMock()
    return mock_repo_files_repository


@pytest.fixture()
def pii_scanner_service(mock_repo_files_repository: MagicMock) -> PiiScannerService:
    return PiiScannerService(mock_repo_files_repository)


# dummy test below as placeholder
def test_that_pii_scanner_service_does_cool_things(
    pii_scanner_service: PiiScannerService,
):
    pass

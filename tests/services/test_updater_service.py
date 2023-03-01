from unittest.mock import MagicMock

import pytest

from secureli.abstractions.pre_commit import ExecuteResult
from secureli.services.updater import UpdaterService


@pytest.fixture()
def updater_service(mock_pre_commit: MagicMock) -> UpdaterService:
    return UpdaterService(mock_pre_commit)


##### install_hooks #####
def test_that_updater_service_install_hooks_updates_and_prunes_with_pre_commit(
    updater_service: UpdaterService,
    mock_pre_commit: MagicMock,
):
    output = "Some update occurred"
    mock_pre_commit.install_hooks.return_value = ExecuteResult(
        successful=True, output=output
    )
    mock_pre_commit.remove_unused_hooks.return_value = ExecuteResult(
        successful=True, output=output
    )
    update_result = updater_service.install_hooks()

    mock_pre_commit.install_hooks.assert_called_once()
    mock_pre_commit.remove_unused_hooks.assert_called_once()
    assert update_result.successful


def test_that_updater_service_install_hooks_does_not_prune_if_no_updates(
    updater_service: UpdaterService,
    mock_pre_commit: MagicMock,
):
    output = ""
    mock_pre_commit.install_hooks.return_value = ExecuteResult(
        successful=True, output=output
    )
    mock_pre_commit.remove_unused_hooks.return_value = ExecuteResult(
        successful=True, output=output
    )
    update_result = updater_service.install_hooks()

    mock_pre_commit.install_hooks.assert_called_once()
    mock_pre_commit.remove_unused_hooks.assert_not_called()
    assert update_result.successful


##### update_hooks #####
def test_that_updater_service_update_hooks_updates_with_pre_commit(
    updater_service: UpdaterService,
    mock_pre_commit: MagicMock,
):
    output = "Some update occurred"
    mock_pre_commit.autoupdate_hooks.return_value = ExecuteResult(
        successful=True, output=output
    )
    mock_pre_commit.remove_unused_hooks.return_value = ExecuteResult(
        successful=True, output=output
    )
    update_result = updater_service.update_hooks()

    mock_pre_commit.autoupdate_hooks.assert_called_once()
    assert update_result.successful

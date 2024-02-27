from unittest.mock import MagicMock
from pathlib import Path
import pytest

from secureli.abstractions.pre_commit import ExecuteResult
from secureli.services.updater import UpdaterService

test_folder_path = Path("does-not-matter")


@pytest.fixture()
def updater_service(
    mock_pre_commit: MagicMock, mock_secureli_config: MagicMock
) -> UpdaterService:
    return UpdaterService(pre_commit=mock_pre_commit, config=mock_secureli_config)


##### update #####
def test_that_updater_service_update_updates_and_prunes_with_pre_commit(
    updater_service: UpdaterService,
    mock_pre_commit: MagicMock,
):
    output = "Some update occurred"
    mock_pre_commit.update.return_value = ExecuteResult(successful=True, output=output)
    mock_pre_commit.remove_unused_hooks.return_value = ExecuteResult(
        successful=True, output=output
    )
    update_result = updater_service.update(test_folder_path)

    mock_pre_commit.update.assert_called_once()
    mock_pre_commit.remove_unused_hooks.assert_called_once()
    assert update_result.successful


def test_that_updater_service_update_does_not_prune_if_no_updates(
    updater_service: UpdaterService,
    mock_pre_commit: MagicMock,
):
    output = ""
    mock_pre_commit.update.return_value = ExecuteResult(successful=True, output=output)
    mock_pre_commit.remove_unused_hooks.return_value = ExecuteResult(
        successful=True, output=output
    )
    update_result = updater_service.update(test_folder_path)

    mock_pre_commit.update.assert_called_once()
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
    update_result = updater_service.update_hooks(test_folder_path)

    mock_pre_commit.autoupdate_hooks.assert_called_once()
    mock_pre_commit.remove_unused_hooks.assert_called_once()
    assert update_result.successful


def test_that_updater_service_update_hooks_handles_no_updates_successfully(
    updater_service: UpdaterService,
    mock_pre_commit: MagicMock,
):
    output = ""
    mock_pre_commit.autoupdate_hooks.return_value = ExecuteResult(
        successful=True, output=output
    )
    mock_pre_commit.remove_unused_hooks.return_value = ExecuteResult(
        successful=True, output=output
    )
    update_result = updater_service.update_hooks(test_folder_path)

    mock_pre_commit.autoupdate_hooks.assert_called_once()
    mock_pre_commit.remove_unused_hooks.assert_not_called()
    assert update_result.successful

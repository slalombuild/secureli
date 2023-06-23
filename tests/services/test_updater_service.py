from unittest.mock import MagicMock

import pytest

from secureli.services.language_support import ExecuteResult, LanguageMetadata
from secureli.services.updater import UpdaterService


@pytest.fixture()
def updater_service(
    mock_language_support: MagicMock, mock_secureli_config: MagicMock
) -> UpdaterService:
    return UpdaterService(
        language_support=mock_language_support, config=mock_secureli_config
    )


##### update #####
def test_that_updater_service_update_updates_and_prunes_with_language_support(
    updater_service: UpdaterService,
    mock_language_support: MagicMock,
):
    output = "Some update occurred"
    mock_language_support.update.return_value = ExecuteResult(
        successful=True, output=output
    )
    mock_language_support.remove_unused_hooks.return_value = ExecuteResult(
        successful=True, output=output
    )
    update_result = updater_service.update()

    mock_language_support.update.assert_called_once()
    mock_language_support.remove_unused_hooks.assert_called_once()
    assert update_result.successful


def test_that_updater_service_update_does_not_prune_if_no_updates(
    updater_service: UpdaterService,
    mock_language_support: MagicMock,
):
    output = ""
    mock_language_support.update.return_value = ExecuteResult(
        successful=True, output=output
    )
    mock_language_support.remove_unused_hooks.return_value = ExecuteResult(
        successful=True, output=output
    )
    update_result = updater_service.update()

    mock_language_support.update.assert_called_once()
    mock_language_support.remove_unused_hooks.assert_not_called()
    assert update_result.successful


def test_that_updater_service_update_handles_failure_to_update_config(
    updater_service: UpdaterService,
    mock_language_support: MagicMock,
):
    output = ""
    mock_language_support.apply_support.return_value = LanguageMetadata(
        version=None, security_hook_id=None
    )

    update_result = updater_service.update()

    mock_language_support.apply_support.assert_called_once()
    mock_language_support.update.assert_not_called()
    mock_language_support.remove_unused_hooks.assert_not_called()
    assert not update_result.successful == ""


##### update_hooks #####
def test_that_updater_service_update_hooks_updates_with_pre_commit(
    updater_service: UpdaterService,
    mock_language_support: MagicMock,
):
    output = "Some update occurred"
    mock_language_support.autoupdate_hooks.return_value = ExecuteResult(
        successful=True, output=output
    )
    mock_language_support.remove_unused_hooks.return_value = ExecuteResult(
        successful=True, output=output
    )
    update_result = updater_service.update_hooks()

    mock_language_support.autoupdate_hooks.assert_called_once()
    assert update_result.successful


def test_that_updater_service_update_hooks_handles_no_updates_successfully(
    updater_service: UpdaterService,
    mock_language_support: MagicMock,
):
    output = ""
    mock_language_support.autoupdate_hooks.return_value = ExecuteResult(
        successful=True, output=output
    )
    mock_language_support.remove_unused_hooks.return_value = ExecuteResult(
        successful=True, output=output
    )
    update_result = updater_service.update_hooks()

    mock_language_support.autoupdate_hooks.assert_called_once()
    assert update_result.successful

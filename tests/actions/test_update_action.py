from unittest.mock import MagicMock

import pytest

from secureli.actions.action import ActionDependencies
from secureli.actions.update import UpdateAction
from secureli.services.updater import UpdateResult


@pytest.fixture()
def mock_scanner() -> MagicMock:
    mock_scanner = MagicMock()
    return mock_scanner


@pytest.fixture()
def mock_updater() -> MagicMock:
    mock_updater = MagicMock()
    mock_updater.update_hooks.return_value = UpdateResult(successful=True)
    mock_updater.update.return_value = UpdateResult(successful=True)
    return mock_updater


@pytest.fixture()
def action_deps(
    mock_echo: MagicMock,
    mock_language_analyzer: MagicMock,
    mock_language_support: MagicMock,
    mock_scanner: MagicMock,
    mock_secureli_config: MagicMock,
    mock_updater: MagicMock,
    mock_pre_commit: MagicMock,
) -> ActionDependencies:
    return ActionDependencies(
        mock_echo,
        mock_language_analyzer,
        mock_language_support,
        mock_scanner,
        mock_secureli_config,
        mock_updater,
        mock_pre_commit,
    )


@pytest.fixture()
def update_action(
    action_deps: ActionDependencies,
    mock_logging_service: MagicMock,
    mock_updater: MagicMock,
) -> UpdateAction:
    return UpdateAction(
        action_deps=action_deps,
        echo=action_deps.echo,
        logging=mock_logging_service,
        updater=mock_updater,
    )


def test_that_update_action_executes_successfully(
    update_action: UpdateAction,
    mock_updater: MagicMock,
    mock_echo: MagicMock,
):
    mock_updater.update.return_value = UpdateResult(
        successful=True, output="Some update performed"
    )

    update_action.update_hooks()

    mock_echo.print.assert_called_with("Update executed successfully.")


def test_that_update_action_handles_failed_execution(
    update_action: UpdateAction,
    mock_updater: MagicMock,
    mock_echo: MagicMock,
):
    mock_updater.update.return_value = UpdateResult(
        successful=False, output="Failed to update"
    )

    update_action.update_hooks()

    mock_echo.print.assert_called_with("Failed to update")


def test_that_latest_flag_initiates_update(
    update_action: UpdateAction,
    mock_echo: MagicMock,
):
    update_action.update_hooks(latest=True)

    mock_echo.print.assert_called_with("Hooks successfully updated to latest version")


def test_that_latest_flag_handles_failed_update(
    update_action: UpdateAction,
    mock_updater: MagicMock,
    mock_echo: MagicMock,
):
    mock_updater.update_hooks.return_value = UpdateResult(
        successful=False, output="Update failed"
    )
    update_action.update_hooks(latest=True)

    mock_echo.print.assert_called_with("Update failed")

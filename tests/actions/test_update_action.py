from unittest.mock import MagicMock
from pathlib import Path
import pytest

from secureli.actions.action import ActionDependencies
from secureli.actions.update import UpdateAction
from secureli.modules.shared.models.repository import CustomScanSettings, SecureliFile
from secureli.modules.shared.models.update import UpdateResult

test_folder_path = Path("does-not-matter")


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
    mock_settings: MagicMock,
    mock_updater: MagicMock,
    mock_logging_service: MagicMock,
) -> ActionDependencies:
    return ActionDependencies(
        mock_echo,
        mock_language_analyzer,
        mock_language_support,
        mock_scanner,
        mock_secureli_config,
        mock_settings,
        mock_updater,
        mock_logging_service,
    )


@pytest.fixture()
def update_action(
    action_deps: ActionDependencies,
    mock_updater: MagicMock,
) -> UpdateAction:
    return UpdateAction(
        action_deps=action_deps,
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

    update_action.update_hooks(test_folder_path)

    mock_echo.print.assert_called_with("Update executed successfully.")


def test_that_update_action_handles_failed_execution(
    update_action: UpdateAction,
    mock_updater: MagicMock,
    mock_echo: MagicMock,
):
    mock_updater.update.return_value = UpdateResult(
        successful=False, output="Failed to update"
    )

    update_action.update_hooks(test_folder_path)

    mock_echo.print.assert_called_with("Failed to update")


def test_that_latest_flag_initiates_update(
    update_action: UpdateAction,
    mock_echo: MagicMock,
):
    update_action.update_hooks(test_folder_path, latest=True)

    mock_echo.print.assert_called_with("Hooks successfully updated to latest version")


def test_that_latest_flag_handles_failed_update(
    update_action: UpdateAction,
    mock_updater: MagicMock,
    mock_echo: MagicMock,
):
    mock_updater.update_hooks.return_value = UpdateResult(
        successful=False, output="Update failed"
    )
    update_action.update_hooks(test_folder_path, latest=True)

    mock_echo.print.assert_called_with("Update failed")


# Using a set in the 2nd scenario gets past order problems - not sure if there are other side effects
@pytest.mark.parametrize(
    "patternList",
    [
        [r"^[\w\-\.]+@([\w-]+\.)+[\w-]{2,}$"],
        (
            {
                "test_pattern",
                r"^[\w\-\.]+@([\w-]+\.)+[\w-]{2,}$",
            }
        ),
    ],
)
def test_single_pattern_addition_succeeds(
    update_action: UpdateAction, patternList: list[str]
):
    expected = SecureliFile()
    expected.scan_patterns = CustomScanSettings(custom_scan_patterns=patternList)
    update_action.add_pattern(test_folder_path, patternList)

    update_action.action_deps.settings.save.assert_called_with(expected)
    update_action.action_deps.echo.print.assert_any_call(
        "Current custom scan patterns:"
    )
    update_action.action_deps.echo.print.assert_called_with(list(patternList))


def test_scan_pattern_object_is_initialized(
    update_action: UpdateAction,
):
    patternList = ["Test_pattern"]
    expected = SecureliFile()
    expected.scan_patterns = CustomScanSettings(custom_scan_patterns=patternList)

    mock_secureli_file = SecureliFile()
    mock_secureli_file.scan_patterns = CustomScanSettings(
        custom_scan_patterns=patternList
    )
    update_action.action_deps.settings.load = MagicMock(return_value=mock_secureli_file)

    update_action.add_pattern(test_folder_path, patternList)

    update_action.action_deps.settings.save.assert_called_with(expected)


def test_multiple_patern_addition_partial_success(
    update_action: UpdateAction,
    mock_echo: MagicMock,
):
    valid_pattern = "Test_pattern"
    malformed_pattern = ".[/"
    patternList = [valid_pattern, malformed_pattern]
    expected = SecureliFile()
    expected.scan_patterns = CustomScanSettings(custom_scan_patterns=[valid_pattern])
    update_action.add_pattern(test_folder_path, patternList)

    update_action.action_deps.settings.save.assert_called_with(expected)
    update_action.action_deps.echo.warning.assert_any_call(
        f'Invalid regex pattern detected: "{malformed_pattern}". Excluding pattern.\n'
    )
    update_action.action_deps.echo.print.assert_any_call(
        "Current custom scan patterns:"
    )
    update_action.action_deps.echo.print.assert_called_with([valid_pattern])


def test_malformed_regex_fails(
    update_action: UpdateAction,
):
    malformed_input = [".[/"]
    update_action.add_pattern(test_folder_path, malformed_input)

    update_action.action_deps.echo.warning.assert_called_once_with(
        f'Invalid regex pattern detected: "{malformed_input[0]}". Excluding pattern.\n'
    )


def test_only_one_duplicate_flag_is_added(
    update_action: UpdateAction,
):
    patternList = ["Test_pattern"]
    duplicatedList = patternList * 2
    expected = SecureliFile()
    expected.scan_patterns = CustomScanSettings(custom_scan_patterns=patternList)

    update_action.add_pattern(test_folder_path, duplicatedList)

    update_action.action_deps.settings.save.assert_called_with(expected)
    update_action.action_deps.echo.print.assert_any_call(
        "Current custom scan patterns:"
    )
    update_action.action_deps.echo.print.assert_called_with(patternList)


def test_preexisting_pattern_is_not_added(
    update_action: UpdateAction,
):
    patternList = ["Test_pattern"]
    mock_secureli_file = SecureliFile()
    mock_secureli_file.scan_patterns = CustomScanSettings(
        custom_scan_patterns=patternList
    )
    update_action.action_deps.settings.load = MagicMock(return_value=mock_secureli_file)

    update_action.add_pattern(test_folder_path, patternList)

    update_action.action_deps.settings.save.assert_called_with(mock_secureli_file)
    update_action.action_deps.echo.print.assert_any_call(
        "Current custom scan patterns:"
    )
    update_action.action_deps.echo.print.assert_called_with(patternList)


@pytest.mark.parametrize(
    "pattern,expectedResult", [("Test_pattern", True), ("./[invalid", False)]
)
def test_valid_regex(update_action: UpdateAction, pattern: str, expectedResult: bool):
    assert update_action._validate_regex(pattern) == expectedResult


@pytest.mark.parametrize(
    "pattern,patterns,expectedResult",
    [
        ("Test_pattern", [], True),
        ("Test_pattern", ["Test_pattern"], False),
        ("./[invalid", [], False),
    ],
)
def test_valid_pattern(
    update_action: UpdateAction, pattern: str, patterns: list[str], expectedResult: bool
):
    assert update_action._validate_pattern(pattern, patterns) == expectedResult

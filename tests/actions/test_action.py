from pathlib import Path
from unittest.mock import MagicMock

import pytest

from secureli.abstractions.pre_commit import InstallFailedError
from secureli.repositories.secureli_config import SecureliConfig
from secureli.services.language_analyzer import AnalyzeResult, SkippedFile
from secureli.actions.action import Action, ActionDependencies
from secureli.services.language_support import LanguageMetadata
from secureli.abstractions.pre_commit import ValidateConfigResult

test_folder_path = Path("does-not-matter")


@pytest.fixture()
def mock_scanner() -> MagicMock:
    mock_scanner = MagicMock()
    return mock_scanner


@pytest.fixture()
def mock_updater() -> MagicMock:
    mock_updater = MagicMock()
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
def action(action_deps: ActionDependencies) -> Action:
    return Action(action_deps=action_deps)


def test_that_initialize_repo_raises_value_error_without_any_supported_languages(
    action: Action,
    mock_language_analyzer: MagicMock,
    mock_echo: MagicMock,
):
    mock_language_analyzer.analyze.return_value = AnalyzeResult(
        language_proportions={}, skipped_files=[]
    )

    action.verify_install(test_folder_path, reset=True, always_yes=True)

    mock_echo.error.assert_called_with(
        "SeCureLI could not be installed due to an error: No supported languages found in current repository"
    )


def test_that_initialize_repo_install_flow_selects_rad_lang(
    action: Action,
    mock_language_analyzer: MagicMock,
    mock_echo: MagicMock,
):
    mock_language_analyzer.analyze.return_value = AnalyzeResult(
        language_proportions={
            "RadLang": 0.75,
            "BadLang": 0.25,
        },
        skipped_files=[],
    )

    action.verify_install(test_folder_path, reset=True, always_yes=True)

    mock_echo.print.assert_called_with(
        "SeCureLI has been installed successfully (language = RadLang)"
    )


def test_that_initialize_repo_install_flow_performs_security_analysis(
    action: Action,
    mock_language_analyzer: MagicMock,
    mock_scanner: MagicMock,
):
    mock_language_analyzer.analyze.return_value = AnalyzeResult(
        language_proportions={
            "RadLang": 0.75,
            "BadLang": 0.25,
        },
        skipped_files=[],
    )

    action.verify_install(test_folder_path, reset=True, always_yes=True)

    mock_scanner.scan_repo.assert_called_once()


def test_that_initialize_repo_install_flow_skips_security_analysis_if_unavailable(
    action: Action,
    mock_language_analyzer: MagicMock,
    mock_scanner: MagicMock,
    mock_language_support: MagicMock,
):
    mock_language_analyzer.analyze.return_value = AnalyzeResult(
        language_proportions={
            "RadLang": 0.75,
            "BadLang": 0.25,
        },
        skipped_files=[],
    )
    mock_language_support.apply_support.return_value = LanguageMetadata(
        version="abc123", security_hook_id=None
    )

    action.verify_install(test_folder_path, reset=True, always_yes=True)

    mock_scanner.scan_repo.assert_not_called()


def test_that_initialize_repo_install_flow_warns_about_skipped_files(
    action: Action,
    mock_language_analyzer: MagicMock,
    mock_echo: MagicMock,
):
    mock_language_analyzer.analyze.return_value = AnalyzeResult(
        language_proportions={
            "RadLang": 0.75,
            "BadLang": 0.25,
        },
        skipped_files=[
            SkippedFile(
                file_path=Path("./file.wacky-extension"),
                error_message="What a wacky extension!",
            ),
            SkippedFile(
                file_path=Path("./file2.huge"), error_message="What a huge file!"
            ),
        ],
    )

    action.verify_install(test_folder_path, reset=True, always_yes=True)

    assert (
        mock_echo.warning.call_count == 3
    )  # "2 files skipped" + the two files themselves


def test_that_initialize_repo_can_be_canceled(
    action: Action,
    mock_echo: MagicMock,
):
    mock_echo.confirm.return_value = False

    action.verify_install(test_folder_path, reset=True, always_yes=False)

    mock_echo.error.assert_called_with("User canceled install process")


def test_that_initialize_repo_selects_previously_selected_language(
    action: Action,
    mock_secureli_config: MagicMock,
    mock_language_support: MagicMock,
    mock_echo: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig(
        overall_language="PreviousLang", version_installed="abc123"
    )
    mock_language_support.version_for_language.return_value = "abc123"

    action.verify_install(test_folder_path, reset=False, always_yes=True)

    mock_echo.print.assert_called_once_with(
        "SeCureLI is installed and up-to-date (language = PreviousLang)"
    )


def test_that_initialize_repo_prompts_to_upgrade_when_out_of_sync(
    action: Action,
    mock_secureli_config: MagicMock,
    mock_language_support: MagicMock,
    mock_echo: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig(
        overall_language="PreviousLang", version_installed="abc123"
    )
    mock_language_support.version_for_language.return_value = "xyz987"
    mock_echo.confirm.return_value = False

    action.verify_install(test_folder_path, reset=False, always_yes=False)

    mock_echo.warning.assert_called_with("User canceled upgrade process")


def test_that_initialize_repo_auto_upgrades_when_out_of_sync(
    action: Action,
    mock_secureli_config: MagicMock,
    mock_language_support: MagicMock,
    mock_echo: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig(
        overall_language="PreviousLang", version_installed="abc123"
    )
    mock_language_support.version_for_language.return_value = "xyz987"

    action.verify_install(test_folder_path, reset=False, always_yes=True)

    mock_echo.print.assert_called_with("SeCureLI has been upgraded successfully")


def test_that_initialize_repo_reports_errors_when_upgrade_fails(
    action: Action,
    mock_secureli_config: MagicMock,
    mock_language_support: MagicMock,
    mock_echo: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig(
        overall_language="PreviousLang", version_installed="abc123"
    )
    mock_language_support.version_for_language.return_value = "xyz987"
    mock_language_support.apply_support.side_effect = InstallFailedError

    action.verify_install(test_folder_path, reset=False, always_yes=True)

    mock_echo.error.assert_called_with("SeCureLI could not be upgraded due to an error")


def test_that_initialize_repo_is_aborted_by_the_user_if_the_process_is_canceled(
    action: Action,
    mock_secureli_config: MagicMock,
    mock_language_support: MagicMock,
    mock_echo: MagicMock,
):
    # User elects to cancel the process, overridden if yes=True on the initializer
    mock_echo.confirm.return_value = False
    mock_secureli_config.load.return_value = SecureliConfig()  # fresh config

    action.verify_install(test_folder_path, reset=False, always_yes=False)

    mock_echo.error.assert_called_with("User canceled install process")


def test_that_verify_install_updates_if_config_validation_fails(
    action: Action,
    mock_pre_commit: MagicMock,
    mock_language_support: MagicMock,
):
    mock_pre_commit.validate_config.return_value = ValidateConfigResult(
        successful=False, output="Configs don't match"
    )
    mock_language_support.apply_support.return_value = LanguageMetadata(
        version="abc123", security_hook_id=None
    )

    verify_result = action.verify_install(
        test_folder_path, reset=False, always_yes=True
    )

    assert verify_result.outcome == "upgrade-succeeded"

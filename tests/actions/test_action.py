from pathlib import Path
from unittest.mock import MagicMock

import pytest

from secureli.actions.action import Action, ActionDependencies, VerifyOutcome
from secureli.repositories.secureli_config import SecureliConfig, VerifyConfigOutcome
from secureli.services.language_analyzer import AnalyzeResult, SkippedFile
from secureli.services.language_support import LanguageMetadata
from secureli.services.scanner import ScanResult, Failure
from secureli.services.updater import UpdateResult

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
) -> ActionDependencies:
    return ActionDependencies(
        mock_echo,
        mock_language_analyzer,
        mock_language_support,
        mock_scanner,
        mock_secureli_config,
        None,
        mock_updater,
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
        "seCureLI could not be installed due to an error: No supported languages found in current repository"
    )


def test_that_initialize_repo_install_flow_selects_both_languages(
    action: Action,
    mock_language_analyzer: MagicMock,
    mock_echo: MagicMock,
):
    mock_language_analyzer.analyze.return_value = AnalyzeResult(
        language_proportions={
            "RadLang": 0.75,
            "CoolLang": 0.25,
        },
        skipped_files=[],
    )

    action.verify_install(test_folder_path, reset=True, always_yes=True)

    mock_echo.print.assert_called_with(
        "seCureLI has been installed successfully (languages = ['RadLang', 'CoolLang'])"
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


def test_that_initialize_repo_install_flow_displays_security_analysis_results(
    action: Action, action_deps: MagicMock, mock_scanner: MagicMock
):
    mock_scanner.scan_repo.return_value = ScanResult(
        successful=False,
        output="Detect secrets...Failed",
        failures=[Failure(repo="repo", id="id", file="file")],
    )
    action.verify_install(test_folder_path, reset=True, always_yes=True)

    action_deps.echo.print.assert_any_call("Detect secrets...Failed")


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
        languages=["PreviousLang"], version_installed="abc123"
    )
    mock_language_support.version_for_language.return_value = "abc123"

    action.verify_install(test_folder_path, reset=False, always_yes=True)

    mock_echo.print.assert_called_once_with(
        "seCureLI is installed and up-to-date (languages = ['PreviousLang'])"
    )


def test_that_initialize_repo_prompts_to_upgrade_config_if_old_schema(
    action: Action,
    mock_secureli_config: MagicMock,
    mock_language_support: MagicMock,
    mock_echo: MagicMock,
):
    mock_secureli_config.verify.return_value = VerifyConfigOutcome.OUT_OF_DATE

    mock_language_support.version_for_language.return_value = "xyz987"
    mock_echo.confirm.return_value = False

    action.verify_install(test_folder_path, reset=False, always_yes=False)

    mock_echo.error.assert_called_with("seCureLI could not be verified.")


def test_that_initialize_repo_updates_repo_config_if_old_schema(
    action: Action,
    mock_secureli_config: MagicMock,
    mock_language_support: MagicMock,
    mock_echo: MagicMock,
):
    mock_secureli_config.verify.return_value = VerifyConfigOutcome.OUT_OF_DATE

    mock_secureli_config.update.return_value = SecureliConfig(
        languages=["PreviousLang"], version_installed="abc123"
    )

    mock_secureli_config.load.return_value = SecureliConfig(
        languages=["PreviousLang"], version_installed="abc123"
    )

    mock_language_support.version_for_language.return_value = "abc123"

    result = action.verify_install(test_folder_path, reset=False, always_yes=True)

    assert result.outcome == VerifyOutcome.UP_TO_DATE


def test_that_initialize_repo_reports_errors_when_schema_upgdate_fails(
    action: Action,
    mock_secureli_config: MagicMock,
    mock_language_support: MagicMock,
    mock_echo: MagicMock,
):
    mock_secureli_config.verify.return_value = VerifyConfigOutcome.OUT_OF_DATE

    mock_secureli_config.update.side_effect = Exception

    action.verify_install(test_folder_path, reset=False, always_yes=True)

    mock_echo.error.assert_called_with("seCureLI could not be verified.")


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


def test_that_update_secureli_handles_declined_update(
    action: Action,
    mock_echo: MagicMock,
):
    mock_echo.confirm.return_value = False
    update_result = action._update_secureli(always_yes=False)

    assert update_result.outcome == VerifyOutcome.UPDATE_CANCELED


def test_that_update_secureli_handles_failed_update(
    action: Action,
    mock_updater: MagicMock,
):
    mock_updater.update.return_value = UpdateResult(
        successful=False, outcome=VerifyOutcome.UPDATE_FAILED
    )
    update_result = action._update_secureli(always_yes=False)

    assert update_result.outcome == VerifyOutcome.UPDATE_FAILED


def test_that_update_secureli_handles_successful_update(
    action: Action,
    mock_updater: MagicMock,
):
    mock_updater.update.return_value = UpdateResult(
        successful=True, outcome=VerifyOutcome.UPDATE_SUCCEEDED
    )
    update_result = action._update_secureli(always_yes=False)

    assert update_result.outcome == VerifyOutcome.UPDATE_SUCCEEDED


def test_that_prompt_get_lint_config_languages_returns_all_languages_when_always_true_option_is_true(
    action: Action,
    mock_echo: MagicMock,
):
    mock_languages = ["RadLang", "MockLang"]

    result = action._prompt_get_lint_config_languages(mock_languages, True)

    mock_echo.confirm.assert_not_called()
    assert result == set(mock_languages)


def test_that_prompt_get_lint_config_languages_returns_no_languages(
    action: Action,
    mock_echo: MagicMock,
):
    mock_languages = ["RadLang", "MockLang"]
    mock_echo.confirm.return_value = False

    result = action._prompt_get_lint_config_languages(mock_languages, False)

    mock_echo.confirm.assert_called()
    assert mock_echo.confirm.call_count == len(mock_languages)
    assert result == set()


def test_that_prompt_get_lint_config_languages_returns_all_languages(
    action: Action,
    mock_echo: MagicMock,
):
    mock_languages = ["RadLang", "MockLang"]
    mock_echo.confirm.return_value = True

    result = action._prompt_get_lint_config_languages(mock_languages, False)

    mock_echo.confirm.assert_called()
    assert mock_echo.confirm.call_count == len(mock_languages)
    assert result == set(mock_languages)


def test_that_prompt_get_lint_config_languages_returns_filtered_languages_based_on_choice(
    action: Action,
    mock_echo: MagicMock,
):
    mock_languages = ["RadLang", "MockLang"]

    def confirm_side_effect(*args, **kwargs):
        if mock_languages[0] in args[0]:
            return True
        else:
            return False

    mock_echo.confirm.side_effect = confirm_side_effect

    result = action._prompt_get_lint_config_languages(mock_languages, False)

    mock_echo.confirm.assert_called()
    assert mock_echo.confirm.call_count == len(mock_languages)
    assert result == set([mock_languages[0]])

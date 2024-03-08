from pathlib import Path
from unittest.mock import MagicMock

import pytest
from secureli.modules.shared.abstractions.pre_commit import InstallResult

from secureli.actions.action import Action, ActionDependencies
from secureli.modules.observability.consts.logging import TELEMETRY_DEFAULT_ENDPOINT
from secureli.modules.shared.models.echo import Color
from secureli.modules.shared.models.install import VerifyOutcome
from secureli.modules.shared.models import language
from secureli.modules.shared.models.scan import ScanFailure, ScanResult
from secureli.repositories.secureli_config import SecureliConfig, VerifyConfigOutcome
from secureli.modules.core.core_services.updater import UpdateResult

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
    mock_settings: MagicMock,
) -> ActionDependencies:
    return ActionDependencies(
        mock_echo,
        mock_language_analyzer,
        mock_language_support,
        mock_scanner,
        mock_secureli_config,
        mock_settings,
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
    mock_language_analyzer.analyze.return_value = language.AnalyzeResult(
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
    mock_language_analyzer.analyze.return_value = language.AnalyzeResult(
        language_proportions={
            "RadLang": 0.75,
            "CoolLang": 0.25,
        },
        skipped_files=[],
    )

    action.verify_install(test_folder_path, reset=True, always_yes=True)

    mock_echo.print.assert_called_with(
        "seCureLI has been installed successfully for the following language(s): RadLang and CoolLang.\n",
        color=Color.CYAN,
        bold=True,
    )


def test_that_initialize_repo_install_flow_performs_security_analysis(
    action: Action,
    mock_language_analyzer: MagicMock,
    mock_scanner: MagicMock,
):
    mock_language_analyzer.analyze.return_value = language.AnalyzeResult(
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
        failures=[ScanFailure(repo="repo", id="id", file="file")],
    )
    action.verify_install(test_folder_path, reset=True, always_yes=True)

    action_deps.echo.print.assert_any_call("Detect secrets...Failed")


def test_that_initialize_repo_install_flow_skips_security_analysis_if_unavailable(
    action: Action,
    mock_language_analyzer: MagicMock,
    mock_scanner: MagicMock,
    mock_language_support: MagicMock,
):
    mock_language_analyzer.analyze.return_value = language.AnalyzeResult(
        language_proportions={
            "RadLang": 0.75,
            "BadLang": 0.25,
        },
        skipped_files=[],
    )
    mock_language_support.apply_support.return_value = language.LanguageMetadata(
        version="abc123", security_hook_id=None
    )

    action.verify_install(test_folder_path, reset=True, always_yes=True)

    mock_scanner.scan_repo.assert_not_called()


def test_that_initialize_repo_install_flow_warns_about_skipped_files(
    action: Action,
    mock_language_analyzer: MagicMock,
    mock_echo: MagicMock,
    mock_updater: MagicMock,
):
    mock_language_analyzer.analyze.return_value = language.AnalyzeResult(
        language_proportions={
            "RadLang": 0.75,
            "BadLang": 0.25,
        },
        skipped_files=[
            language.SkippedFile(
                file_path=Path("./file.wacky-extension"),
                error_message="What a wacky extension!",
            ),
            language.SkippedFile(
                file_path=Path("./file2.huge"), error_message="What a huge file!"
            ),
        ],
    )

    mock_updater.pre_commit.install.return_value = InstallResult(
        successful=True, backup_hook_path=None
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
    mock_language_analyzer: MagicMock,
):
    mock_language_analyzer.analyze.return_value = language.AnalyzeResult(
        language_proportions={"PreviousLang": 1.0},
        skipped_files=[],
    )
    mock_secureli_config.load.return_value = SecureliConfig(
        languages=["PreviousLang"], version_installed="abc123"
    )
    mock_language_support.version_for_language.return_value = "abc123"

    action.verify_install(test_folder_path, reset=False, always_yes=True)

    mock_echo.print.assert_called_with(
        "seCureLI is installed and up-to-date for the following language(s): PreviousLang"
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
    mock_language_analyzer: MagicMock,
):
    mock_language_analyzer.analyze.return_value = language.AnalyzeResult(
        language_proportions={"PreviousLang": 1.0},
        skipped_files=[],
    )
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


def test_that_initialize_repo_reports_errors_when_schema_update_fails(
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


def test_that_initialize_repo_returns_up_to_date_if_the_process_is_canceled_on_existing_install(
    action: Action,
    mock_secureli_config: MagicMock,
    mock_language_analyzer: MagicMock,
    mock_echo: MagicMock,
):
    # User elects to cancel the process
    mock_echo.confirm.return_value = False
    mock_secureli_config.load.return_value = SecureliConfig(
        languages=["RadLang"], version_installed="abc123"
    )
    mock_language_analyzer.analyze.return_value = language.AnalyzeResult(
        language_proportions={"RadLang": 0.5, "CoolLang": 0.5}, skipped_files=[]
    )

    result = action.verify_install(test_folder_path, reset=False, always_yes=False)
    assert result.outcome == VerifyOutcome.UP_TO_DATE


def test_that_initialize_repo_prints_warnings_for_failed_linter_config_writes(
    action: Action,
    mock_language_support: MagicMock,
    mock_echo: MagicMock,
    mock_updater: MagicMock,
):
    config_write_error = "Failed to write config file for RadLang"

    mock_language_support.apply_support.return_value = language.LanguageMetadata(
        version="abc123",
        security_hook_id="test_hook_id",
        linter_config_write_errors=[config_write_error],
    )

    mock_updater.pre_commit.install.return_value = InstallResult(
        successful=True, backup_hook_path=None
    )

    action.verify_install(test_folder_path, reset=True, always_yes=True)

    mock_echo.warning.assert_called_once_with(config_write_error)


def test_that_verify_install_returns_failed_result_on_new_install_language_not_supported(
    action: Action,
    mock_secureli_config: MagicMock,
    mock_language_analyzer: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig(
        languages=[], version_installed=None
    )

    mock_language_analyzer.analyze.return_value = language.AnalyzeResult(
        language_proportions={}, skipped_files=[]
    )

    verify_result = action.verify_install(
        test_folder_path, reset=False, always_yes=False
    )

    assert verify_result.outcome == VerifyOutcome.INSTALL_FAILED


def test_that_verify_install_returns_up_to_date_result_on_existing_install_languages_not_supported(
    action: Action,
    mock_secureli_config: MagicMock,
    mock_language_analyzer: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig(
        languages=["RadLang"], version_installed="abc123"
    )

    mock_language_analyzer.analyze.return_value = language.AnalyzeResult(
        language_proportions={}, skipped_files=[]
    )

    verify_result = action.verify_install(
        test_folder_path, reset=False, always_yes=False
    )

    assert verify_result.outcome == VerifyOutcome.UP_TO_DATE


def test_that_verify_install_returns_up_to_date_result_on_existing_install_no_new_languages(
    action: Action,
    mock_secureli_config: MagicMock,
    mock_language_analyzer: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig(
        languages=["RadLang"], version_installed="abc123"
    )

    mock_language_analyzer.analyze.return_value = language.AnalyzeResult(
        language_proportions={"RadLang": 1.0}, skipped_files=[]
    )

    verify_result = action.verify_install(
        test_folder_path, reset=False, always_yes=False
    )

    assert verify_result.outcome == VerifyOutcome.UP_TO_DATE


def test_that_verify_install_returns_success_result_newly_detected_language_install(
    action: Action,
    mock_secureli_config: MagicMock,
    mock_language_analyzer: MagicMock,
):
    mock_secureli_config.load.return_value = SecureliConfig(
        languages=["RadLang"], version_installed="abc123"
    )

    mock_language_analyzer.analyze.return_value = language.AnalyzeResult(
        language_proportions={"RadLang": 0.5, "CoolLang": 0.5}, skipped_files=[]
    )

    verify_result = action.verify_install(
        test_folder_path, reset=False, always_yes=True
    )

    assert verify_result.outcome == VerifyOutcome.INSTALL_SUCCEEDED


def test_that_initialize_repo_install_flow_warns_about_overwriting_pre_commit_file(
    action: Action,
    mock_language_analyzer: MagicMock,
    mock_echo: MagicMock,
    mock_updater: MagicMock,
):
    mock_language_analyzer.analyze.return_value = language.AnalyzeResult(
        language_proportions={
            "RadLang": 0.75,
        },
        skipped_files=[],
    )

    install_result = InstallResult(
        successful=True, backup_hook_path="pre-commit.backup"
    )

    mock_updater.pre_commit.install.return_value = install_result

    action.verify_install(test_folder_path, reset=True, always_yes=True)

    mock_echo.warning.assert_called_once_with(
        (
            (
                "An existing pre-commit hook file has been detected at /.git/hooks/pre-commit\n"
                "A backup file has been created and the existing file has been overwritten\n"
                f"Backup file: {install_result.backup_hook_path}"
            )
        )
    )


def test_that_update_secureli_handles_declined_update(
    action: Action,
    mock_echo: MagicMock,
):
    mock_echo.confirm.return_value = False
    update_result = action._update_secureli(always_yes=False)

    assert update_result.outcome == VerifyOutcome.UPDATE_CANCELED


def test_that_update_secureli_handles_failed_update(
    action: Action, mock_updater: MagicMock, mock_echo: MagicMock
):
    mock_updater.update.return_value = UpdateResult(
        successful=False, outcome=VerifyOutcome.UPDATE_FAILED
    )
    update_result = action._update_secureli(always_yes=False)

    mock_echo.print.assert_not_called()
    assert update_result.outcome == VerifyOutcome.UPDATE_FAILED


def test_that_update_secureli_handles_successful_update(
    action: Action, mock_updater: MagicMock, mock_echo: MagicMock
):
    mock_update_result_output = "mock_output"
    mock_updater.update.return_value = UpdateResult(
        successful=True,
        outcome=VerifyOutcome.UPDATE_SUCCEEDED,
        output=mock_update_result_output,
    )
    update_result = action._update_secureli(always_yes=False)

    mock_echo.print.assert_called_once_with(mock_update_result_output)
    assert update_result.outcome == VerifyOutcome.UPDATE_SUCCEEDED


def test_that_prompt_get_lint_config_languages_returns_all_languages_when_always_true_option_is_true(
    action: Action,
    mock_echo: MagicMock,
):
    mock_languages = ["RadLang", "MockLang"]

    result = action._prompt_get_lint_config_languages(mock_languages, True)

    mock_echo.confirm.assert_not_called()
    assert result == mock_languages


def test_that_prompt_get_lint_config_languages_returns_no_languages(
    action: Action,
    mock_echo: MagicMock,
):
    mock_languages = ["RadLang", "MockLang"]
    mock_echo.confirm.return_value = False

    result = action._prompt_get_lint_config_languages(mock_languages, False)

    mock_echo.confirm.assert_called()
    assert mock_echo.confirm.call_count == len(mock_languages)
    assert result == []


def test_that_prompt_get_lint_config_languages_returns_all_languages(
    action: Action,
    mock_echo: MagicMock,
):
    mock_languages = ["RadLang", "MockLang"]
    mock_echo.confirm.return_value = True

    result = action._prompt_get_lint_config_languages(mock_languages, False)

    mock_echo.confirm.assert_called()
    assert mock_echo.confirm.call_count == len(mock_languages)
    assert result == mock_languages


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
    assert result == [mock_languages[0]]


def test_that_prompt_to_install_asks_new_install_msg(
    action: Action, mock_echo: MagicMock
):
    mock_languages = ["RadLang", "CoolLang"]
    action._prompt_to_install(mock_languages, always_yes=False, new_install=True)

    mock_echo.confirm.assert_called_once_with(
        "seCureLI has not yet been installed, install now?", default_response=True
    )


def test_that_prompt_to_install_asks_add_languages_install_msg(
    action: Action, mock_echo: MagicMock
):
    mock_languages = ["RadLang", "CoolLang"]
    action._prompt_to_install(mock_languages, always_yes=False, new_install=False)

    mock_echo.confirm.assert_called_once_with(
        f"seCureLI has not been installed for the following language(s): RadLang and CoolLang, install now?",
        default_response=True,
    )


def test_that_prompt_to_install_does_not_prompt_if_always_yes(
    action: Action, mock_echo: MagicMock
):
    mock_languages = ["RadLang", "CoolLang"]
    result = action._prompt_to_install(
        mock_languages, always_yes=True, new_install=False
    )

    assert result == True
    mock_echo.confirm.not_called()


def test_that_post_install_scan_creates_pre_commit_on_new_install(
    action: Action, mock_updater: MagicMock
):
    action._run_post_install_scan(
        "test/path", SecureliConfig(), language.LanguageMetadata(version="0.03"), True
    )

    mock_updater.pre_commit.install.assert_called_once()


def test_that_post_install_scan_ignores_creating_pre_commit_on_existing_install(
    action: Action, mock_updater: MagicMock
):
    action._run_post_install_scan(
        "test/path", SecureliConfig(), language.LanguageMetadata(version="0.03"), False
    )

    mock_updater.pre_commit.install.assert_not_called()


def test_that_post_install_scan_scans_repo(
    action: Action, mock_scanner: MagicMock, mock_echo: MagicMock
):
    action._run_post_install_scan(
        "test/path",
        SecureliConfig(),
        language.LanguageMetadata(version="0.03", security_hook_id="secrets-hook"),
        False,
    )

    mock_scanner.scan_repo.assert_called_once()
    mock_echo.warning.assert_not_called()


def test_that_post_install_scan_does_not_scan_repo_when_no_security_hook_id(
    action: Action, mock_scanner: MagicMock, mock_echo: MagicMock
):
    action._run_post_install_scan(
        "test/path",
        SecureliConfig(languages=["RadLang"]),
        language.LanguageMetadata(version="0.03"),
        False,
    )

    mock_scanner.scan_repo.assert_not_called()
    mock_echo.warning.assert_called_once_with(
        "RadLang does not support secrets detection, skipping"
    )


def test_that_install_saves_settings(
    action: Action, mock_language_analyzer: MagicMock, mock_settings: MagicMock
):
    mock_language_analyzer.analyze.return_value = language.AnalyzeResult(
        language_proportions={"PreviousLang": 1.0},
        skipped_files=[],
    )
    action._install_secureli("test/path", ["RadLang"], [], True)


def test_that_prompt_get_telemetry_api_url_returns_default_endpoint_when_always_yes(
    action: Action,
):
    result = action._prompt_get_telemetry_api_url(True)

    assert result is TELEMETRY_DEFAULT_ENDPOINT


def test_that_prompt_get_telemetry_api_url_returns_prompt_response(
    action: Action, mock_echo: MagicMock
):
    mock_api_endpoint = "test-endpoint"
    mock_echo.prompt.return_value = mock_api_endpoint

    result = action._prompt_get_telemetry_api_url(False)

    assert result is mock_api_endpoint

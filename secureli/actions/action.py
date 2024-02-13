from abc import ABC
from enum import Enum
from pathlib import Path
from typing import Optional
from secureli.abstractions.echo import EchoAbstraction
from secureli.consts.logging import TELEMETRY_DEFAULT_ENDPOINT
from secureli.models.echo import Color
from secureli.repositories.secureli_config import (
    SecureliConfig,
    SecureliConfigRepository,
    VerifyConfigOutcome,
)
from secureli.repositories.settings import SecureliRepository, TelemetrySettings
from secureli.services.language_analyzer import LanguageAnalyzerService, AnalyzeResult
from secureli.services.language_config import LanguageNotSupportedError
from secureli.services.language_support import (
    LanguageMetadata,
    LanguageSupportService,
)
from secureli.services.scanner import ScannerService, ScanMode
from secureli.services.updater import UpdaterService

import pydantic
from secureli.utilities.formatter import format_sentence_list


class VerifyOutcome(str, Enum):
    INSTALL_CANCELED = "install-canceled"
    INSTALL_FAILED = "install-failed"
    INSTALL_SUCCEEDED = "install-succeeded"
    UPDATE_CANCELED = "update-canceled"
    UPDATE_SUCCEEDED = "update-succeeded"
    UPDATE_FAILED = "update-failed"
    UP_TO_DATE = "up-to-date"


class VerifyResult(pydantic.BaseModel):
    """
    The outcomes of performing verification. Actions can use these results
    to decide whether to proceed with their post-initialization actions or not.
    """

    outcome: VerifyOutcome
    config: Optional[SecureliConfig] = None
    analyze_result: Optional[AnalyzeResult] = None


class ActionDependencies:
    """
    Consolidates a growing set of common dependencies so Action adopters can
    focus on their own direct dependencies, while requesting and providing
    this object to the base class.
    """

    def __init__(
        self,
        echo: EchoAbstraction,
        language_analyzer: LanguageAnalyzerService,
        language_support: LanguageSupportService,
        scanner: ScannerService,
        secureli_config: SecureliConfigRepository,
        settings: SecureliRepository,
        updater: UpdaterService,
    ):
        self.echo = echo
        self.language_analyzer = language_analyzer
        self.language_support = language_support
        self.scanner = scanner
        self.secureli_config = secureli_config
        self.settings = settings
        self.updater = updater


class Action(ABC):
    """The base Action class for any action that can analyze, install and update seCureLI's configuration."""

    def __init__(self, action_deps: ActionDependencies):
        self.action_deps = action_deps

    def verify_install(
        self, folder_path: Path, reset: bool, always_yes: bool
    ) -> VerifyResult:
        """
        Installs, upgrades or verifies the current seCureLI installation
        :param folder_path: The folder path to initialize the repo for
        :param reset: If true, disregard existing configuration and start fresh
        :param always_yes: Assume "Yes" to all prompts
        """

        if self.action_deps.secureli_config.verify() == VerifyConfigOutcome.OUT_OF_DATE:
            update_config = self._update_secureli_config_only(always_yes)
            if update_config.outcome != VerifyOutcome.UPDATE_SUCCEEDED:
                self.action_deps.echo.error(f"seCureLI could not be verified.")
                return VerifyResult(
                    outcome=update_config.outcome,
                )

        config = SecureliConfig() if reset else self.action_deps.secureli_config.load()

        try:
            languages = self._detect_languages(folder_path)
        except (ValueError, LanguageNotSupportedError) as e:
            if config.languages and config.version_installed:
                self.action_deps.echo.warning(
                    f"Newly detected languages are unsupported by seCureLI"
                )
                return VerifyResult(outcome=VerifyOutcome.UP_TO_DATE, config=config)

            self.action_deps.echo.error(
                f"seCureLI could not be installed due to an error: {str(e)}"
            )
            return VerifyResult(
                outcome=VerifyOutcome.INSTALL_FAILED,
            )

        newly_detected_languages = [
            language
            for language in (languages or [])
            if language not in (config.languages or [])
        ]
        if (
            not config.languages
            or not config.version_installed
            or newly_detected_languages
        ):
            return self._install_secureli(
                folder_path, languages, newly_detected_languages, always_yes
            )
        else:
            self.action_deps.echo.print(
                (
                    "seCureLI is installed and up-to-date for the "
                    f"following language(s): {format_sentence_list(languages)}"
                )
            )
            return VerifyResult(
                outcome=VerifyOutcome.UP_TO_DATE,
                config=config,
            )

    def _install_secureli(
        self,
        folder_path: Path,
        detected_languages: list[str],
        install_languages: list[str],
        always_yes: bool,
    ) -> VerifyResult:
        """
        Installs seCureLI into the given folder path and returns the new configuration
        :param folder_path: The folder path to initialize the repo for
        :param detected_languages: list of all languages found in the repo
        :param install_languages: list of specific langugages to install secureli features for
        :param always_yes: Assume "Yes" to all prompts
        :return: The new SecureliConfig after install or None if installation did not complete
        """

        # pre-install
        new_install = len(detected_languages) == len(install_languages)

        should_install = self._prompt_to_install(
            install_languages, always_yes, new_install
        )
        if not should_install:
            if new_install:
                self.action_deps.echo.error("User canceled install process")
                return VerifyResult(
                    outcome=VerifyOutcome.INSTALL_CANCELED,
                )

            self.action_deps.echo.warning("Newly detected languages were not installed")
            return VerifyResult(outcome=VerifyOutcome.UP_TO_DATE)

        settings = self.action_deps.settings.load(folder_path)

        # install
        lint_languages = self._prompt_get_lint_config_languages(
            install_languages, always_yes
        )
        language_config_result = (
            self.action_deps.language_support._build_pre_commit_config(
                install_languages, lint_languages
            )
        )
        metadata = self.action_deps.language_support.apply_support(
            install_languages,
            language_config_result,
            new_install,
        )

        for error_msg in metadata.linter_config_write_errors:
            self.action_deps.echo.warning(error_msg)

        config = SecureliConfig(
            languages=detected_languages,
            version_installed=metadata.version,
        )
        self.action_deps.secureli_config.save(config)

        settings.telemetry = TelemetrySettings(
            api_url=self._prompt_get_telemetry_api_url(always_yes)
        )
        self.action_deps.settings.save(settings)

        # post-install
        self._run_post_install_scan(folder_path, config, metadata, new_install)

        self.action_deps.echo.print(
            (
                "seCureLI has been installed successfully for the following language(s): "
                f"{format_sentence_list(config.languages)}.\n"
            ),
            color=Color.CYAN,
            bold=True,
        )
        return VerifyResult(
            outcome=VerifyOutcome.INSTALL_SUCCEEDED,
            config=config,
        )

    def _prompt_to_install(
        self, languages: list[str], always_yes: bool, new_install: bool
    ) -> bool:
        """
        Prompts user to determine if secureli should be installed or not
        :param languages: List of language names to display
        :param always_yes: Assume "Yes" to all prompts
        :param new_install: Used to determine if the install is new or
        if additional languages are being added
        """

        new_install_message = "seCureLI has not yet been installed, install now?"
        add_languages_message = (
            f"seCureLI has not been installed for the following language(s): "
            f"{format_sentence_list(languages)}, install now?"
        )
        return always_yes or self.action_deps.echo.confirm(
            new_install_message if new_install else add_languages_message,
            default_response=True,
        )

    def _prompt_get_telemetry_api_url(self, always_yes: bool) -> str:
        add_telemetry_message = "Configure endpoint for telemetry logs"
        return (
            TELEMETRY_DEFAULT_ENDPOINT
            if always_yes
            else self.action_deps.echo.prompt(
                add_telemetry_message, TELEMETRY_DEFAULT_ENDPOINT
            )
        )

    def _run_post_install_scan(
        self,
        folder_path: Path,
        config: SecureliConfig,
        metadata: LanguageMetadata,
        new_install: bool,
    ):
        """
        Initializes and runs secrets detection after installation if applicable
        :param folder_path: The folder path for the repo
        :param config: The new config created from the installation
        :param metadata: metadata from the language config that was just installed
        :param new_install: Used to determine if the install is new or
        if additional languages are being added
        """

        if new_install:
            pre_commit_install_result = self.action_deps.updater.pre_commit.install(
                folder_path
            )

            if pre_commit_install_result.backup_hook_path != None:
                self.action_deps.echo.warning(
                    (
                        "An existing pre-commit hook file has been detected at /.git/hooks/pre-commit\n"
                        "A backup file has been created and the existing file has been overwritten\n"
                        f"Backup file: {pre_commit_install_result.backup_hook_path}"
                    )
                )

        if secret_test_id := metadata.security_hook_id:
            self.action_deps.echo.print(
                f"The following language(s) support secrets detection: {format_sentence_list(config.languages)}"
            )
            self.action_deps.echo.print(f"running {secret_test_id}.")

            scan_result = self.action_deps.scanner.scan_repo(
                folder_path,
                ScanMode.ALL_FILES,
                specific_test=secret_test_id,
            )

            self.action_deps.echo.print(f"{scan_result.output}")

        else:
            self.action_deps.echo.warning(
                f"{format_sentence_list(config.languages)} does not support secrets detection, skipping"
            )

    def _detect_languages(self, folder_path: Path) -> list[str]:
        """
        Detects programming languages present in the repository
        :param folder_path: The folder path to initialize the repo for
        :return: A list of all languages found in the repository
        """

        analyze_result = self.action_deps.language_analyzer.analyze(folder_path)

        if analyze_result.skipped_files:
            self.action_deps.echo.warning(
                f"Skipping {len(analyze_result.skipped_files)} file(s):"
            )
        for skipped_file in analyze_result.skipped_files:
            self.action_deps.echo.warning(f"- {skipped_file.error_message}")

        if not analyze_result.language_proportions:
            raise ValueError("No supported languages found in current repository")

        self.action_deps.echo.print(
            "Detected the following language(s):", color=Color.CYAN, bold=True
        )
        for language, percentage in analyze_result.language_proportions.items():
            self.action_deps.echo.print(
                f"- {language}: {percentage:.0%}", color=Color.CYAN, bold=True
            )
        languages = list(analyze_result.language_proportions.keys())

        return languages

    def _prompt_get_lint_config_languages(
        self, languages: list[str], always_yes: bool
    ) -> list[str]:
        """
        Prompts user to add lint pre-commit hooks for each detected language
        :param languages: list of detected languages
        :param always_yes: Assume "Yes" to all prompts
        :return: set of filtered languages to add lint pre-commit hooks for
        """

        if always_yes:
            return [*languages]

        lint_languages: list[str] = []

        for language in languages:
            add_linter = self.action_deps.echo.confirm(
                f"Add lint pre-commit hook(s) for {language}?", default_response=True
            )

            if add_linter:
                lint_languages.append(language)

        return lint_languages

    def _update_secureli(self, always_yes: bool) -> VerifyResult:
        """
        Prompts the user to update to the latest secureli install.
        :param always_yes: Assume "Yes" to all prompts
        :return: Outcome of update
        """
        update_prompt = "Would you like to update your pre-commit configuration to the latest secureli config?\n"
        update_prompt += "This will reset any manual changes that may have been made to the .pre-commit-config.yaml file.\n"
        update_prompt += "Proceed?"
        update_confirmed = always_yes or self.action_deps.echo.confirm(
            update_prompt, default_response=True
        )

        if not update_confirmed:
            self.action_deps.echo.print("\nUpdate declined.\n")
            return VerifyResult(outcome=VerifyOutcome.UPDATE_CANCELED)

        update_result = self.action_deps.updater.update()
        details = update_result.output
        if details:
            self.action_deps.echo.print(details)

        if update_result.successful:
            return VerifyResult(outcome=VerifyOutcome.UPDATE_SUCCEEDED)
        else:
            return VerifyResult(outcome=VerifyOutcome.UPDATE_FAILED)

    def _update_secureli_config_only(self, always_yes: bool) -> VerifyResult:
        self.action_deps.echo.print("seCureLI is using an out-of-date config.")
        response = always_yes or self.action_deps.echo.confirm(
            "Update configuration now?",
            default_response=True,
        )
        if not response:
            self.action_deps.echo.error("User canceled update process")
            return VerifyResult(
                outcome=VerifyOutcome.UPDATE_CANCELED,
            )

        try:
            updated_config = self.action_deps.secureli_config.update()
            self.action_deps.secureli_config.save(updated_config)

            return VerifyResult(outcome=VerifyOutcome.UPDATE_SUCCEEDED)
        except:
            return VerifyResult(outcome=VerifyOutcome.UPDATE_FAILED)

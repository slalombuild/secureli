from abc import ABC
from enum import Enum
from pathlib import Path
from typing import Optional

import pydantic

from secureli.abstractions.echo import EchoAbstraction, Color
from secureli.abstractions.pre_commit import (
    InstallFailedError,
    LanguageNotSupportedError,
)
from secureli.repositories.secureli_config import (
    SecureliConfig,
    SecureliConfigRepository,
)
from secureli.services.language_analyzer import LanguageAnalyzerService, AnalyzeResult
from secureli.services.language_support import LanguageSupportService
from secureli.services.scanner import ScannerService, ScanMode
from secureli.services.updater import UpdaterService
from secureli.abstractions.pre_commit import PreCommitAbstraction


class VerifyOutcome(str, Enum):
    INSTALL_CANCELED = "install-canceled"
    INSTALL_FAILED = "install-failed"
    INSTALL_SUCCEEDED = "install-succeeded"
    UPGRADE_CANCELED = "upgrade-canceled"
    UPGRADE_SUCCEEDED = "upgrade-succeeded"
    UPGRADE_FAILED = "upgrade-failed"
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
        updater: UpdaterService,
        pre_commit: PreCommitAbstraction,
    ):
        self.echo = echo
        self.language_analyzer = language_analyzer
        self.language_support = language_support
        self.scanner = scanner
        self.secureli_config = secureli_config
        self.updater = updater
        self.pre_commit = pre_commit


class Action(ABC):
    """The base Action class for any action that can analyze, install and update SeCureLI's configuration."""

    def __init__(self, action_deps: ActionDependencies):
        self.action_deps = action_deps

    def verify_install(
        self, folder_path: Path, reset: bool, always_yes: bool
    ) -> VerifyResult:
        """
        Installs, upgrades or verifies the current SeCureLI installation
        :param folder_path: The folder path to initialize the repo for
        :param reset: If true, disregard existing configuration and start fresh
        :param always_yes: Assume "Yes" to all prompts
        """

        config = SecureliConfig() if reset else self.action_deps.secureli_config.load()

        if not config.overall_language or not config.version_installed:
            return self._install_secureli(folder_path, always_yes)
        else:
            available_version = self.action_deps.language_support.version_for_language(
                config.overall_language
            )

            # Check for a new version and prompt for upgrade if available
            if available_version != config.version_installed:
                return self._upgrade_secureli(config, available_version, always_yes)

            # Validates the current .pre-commit-config.yaml against the generated config
            config_validation_result = self.action_deps.pre_commit.validate_config(
                language=config.overall_language
            )

            # If config mismatch between available version and current version prompt for upgrade
            if not config_validation_result.successful:
                self.action_deps.echo.print(config_validation_result.output)
                return self._update_secureli(always_yes)

            self.action_deps.echo.print(
                f"SeCureLI is installed and up-to-date (language = {config.overall_language})"
            )
            return VerifyResult(
                outcome=VerifyOutcome.UP_TO_DATE,
                config=config,
            )

    def _upgrade_secureli(
        self, config: SecureliConfig, available_version: str, always_yes: bool
    ) -> VerifyResult:
        """
        Installs SeCureLI into the given folder path and returns the new configuration
        :param config: The existing configuration for SeCureLI
        :param available_version: The new version we're upgrading to
        :param always_yes: Assume "Yes" to all prompts
        :return: The new SecureliConfig after upgrade or None if upgrading did not complete
        """
        self.action_deps.echo.print(
            f"The config version installed is {config.version_installed}, but the latest is {available_version}"
        )
        response = always_yes or self.action_deps.echo.confirm(
            "Upgrade now?",
            default_response=True,
        )
        if not response:
            self.action_deps.echo.warning("User canceled upgrade process")
            return VerifyResult(
                outcome=VerifyOutcome.UPGRADE_CANCELED,
                config=config,
            )

        try:
            metadata = self.action_deps.language_support.apply_support(
                config.overall_language
            )

            # Update config with new version installed and save it
            config.version_installed = metadata.version
            self.action_deps.secureli_config.save(config)
            self.action_deps.echo.print("SeCureLI has been upgraded successfully")
            return VerifyResult(
                outcome=VerifyOutcome.UPGRADE_SUCCEEDED,
                config=config,
            )
        except InstallFailedError:
            self.action_deps.echo.error(
                "SeCureLI could not be upgraded due to an error"
            )
            return VerifyResult(
                outcome=VerifyOutcome.UPGRADE_FAILED,
                config=config,
            )

    def _install_secureli(self, folder_path: Path, always_yes: bool) -> VerifyResult:
        """
        Installs SeCureLI into the given folder path and returns the new configuration
        :param folder_path: The folder path to initialize the repo for
        :param always_yes: Assume "Yes" to all prompts
        :return: The new SecureliConfig after install or None if installation did not complete
        """
        self.action_deps.echo.print("SeCureLI has not been setup yet.")
        response = always_yes or self.action_deps.echo.confirm(
            "Initialize SeCureLI now?",
            default_response=True,
        )
        if not response:
            self.action_deps.echo.error("User canceled install process")
            return VerifyResult(
                outcome=VerifyOutcome.INSTALL_CANCELED,
            )

        try:
            analyze_result = self.action_deps.language_analyzer.analyze(folder_path)

            if analyze_result.skipped_files:
                self.action_deps.echo.warning(
                    f"Skipping {len(analyze_result.skipped_files)} file(s):"
                )
            for skipped_file in analyze_result.skipped_files:
                self.action_deps.echo.warning(f"- {skipped_file.error_message}")

            if not analyze_result.language_proportions:
                raise ValueError("No supported languages found in current repository")

            self.action_deps.echo.print("Detected the following languages:")
            for language, percentage in analyze_result.language_proportions.items():
                self.action_deps.echo.print(
                    f"- {language}: {percentage:.0%}", color=Color.MAGENTA, bold=True
                )
            overall_language = list(analyze_result.language_proportions.keys())[0]
            self.action_deps.echo.print(
                f"Overall Detected Language: {overall_language}"
            )

            metadata = self.action_deps.language_support.apply_support(overall_language)

        except (ValueError, LanguageNotSupportedError, InstallFailedError) as e:
            self.action_deps.echo.error(
                f"SeCureLI could not be installed due to an error: {str(e)}"
            )
            return VerifyResult(
                outcome=VerifyOutcome.INSTALL_FAILED,
            )

        config = SecureliConfig(
            overall_language=overall_language,
            version_installed=metadata.version,
        )
        self.action_deps.secureli_config.save(config)

        if secret_test_id := metadata.security_hook_id:
            self.action_deps.echo.print(
                f"{config.overall_language} supports secrets detection; running {secret_test_id}."
            )
            self.action_deps.scanner.scan_repo(
                ScanMode.ALL_FILES, specific_test=secret_test_id
            )
        else:
            self.action_deps.echo.warning(
                f"{config.overall_language} does not support secrets detection, skipping"
            )

        self.action_deps.echo.print(
            f"SeCureLI has been installed successfully (language = {config.overall_language})"
        )

        return VerifyResult(
            outcome=VerifyOutcome.INSTALL_SUCCEEDED,
            config=config,
            analyze_result=analyze_result,
        )

    def _update_secureli(self, always_yes: bool):
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
        self.action_deps.echo.print(details)

        if update_result.successful:
            return VerifyResult(outcome=VerifyOutcome.UPDATE_SUCCEEDED)
        else:
            return VerifyResult(outcome=VerifyOutcome.UPDATE_FAILED)

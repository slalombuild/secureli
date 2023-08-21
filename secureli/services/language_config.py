from pathlib import Path
from typing import Callable, Any

import pydantic
import yaml

from secureli.resources.slugify import slugify
from secureli.utilities.hash import hash_config
from secureli.utilities.patterns import combine_patterns
import secureli.repositories.secureli_config as SecureliConfig


class LanguageNotSupportedError(Exception):
    """The given language was not supported by the PreCommitHooks abstraction"""

    pass


class LoadLinterConfigsResult(pydantic.BaseModel):
    """Results from finding and loading any pre-commit configs for the language"""

    successful: bool
    linter_data: list[Any]


class LanguagePreCommitResult(pydantic.BaseModel):
    """
    A configuration model for a supported pre-commit-configurable language.
    """

    language: str
    config_data: str
    version: str
    linter_config: LoadLinterConfigsResult


class LanguageConfigService:
    def __init__(
        self,
        command_timeout_seconds: int,
        data_loader: Callable[[str], str],
        ignored_file_patterns: list[str],
    ):
        self.command_timeout_seconds = command_timeout_seconds
        self.data_loader = data_loader
        self.ignored_file_patterns = ignored_file_patterns

    def get_language_config(self, language: str) -> LanguagePreCommitResult:
        """
        Calculates a hash of the pre-commit file for the given language to be used as part
        of the overall installed configuration.
        :param language: The language specified
        :raises LanguageNotSupportedError if the associated pre-commit file for the language is not found
        :return: LanguagePreCommitConfig - A configuration model containing the language,
        config file data, and a versioning hash of the file contents.
        """
        try:
            config_data = self._calculate_combined_configuration_data(language)
            linter_config_data = self._load_linter_config_file(language)

            version = hash_config(config_data)
            return LanguagePreCommitResult(
                language=language,
                config_data=config_data,
                version=version,
                linter_config=linter_config_data,
            )
        except ValueError:
            raise LanguageNotSupportedError(
                f"Language '{language}' is currently unsupported"
            )

    def _calculate_combined_configuration(self, language: str) -> dict:
        """
        Combine elements of our configuration for the specified language along with
        repo settings like ignored file patterns and pre-commit overrides
        :param language: The language to load the configuration for as a basis for
        the combined configuration
        :return: The combined configuration data as a dictionary
        """
        slugified_language = slugify(language)
        config_data = self.data_loader(f"{slugified_language}-pre-commit.yaml")
        config = yaml.safe_load(config_data) or {}
        if self.ignored_file_patterns:
            config["exclude"] = combine_patterns(self.ignored_file_patterns)

        return config

    def _calculate_combined_configuration_data(self, language: str) -> str:
        """
        Combine elements of our configuration for the specified language along with
        repo settings like ignored file patterns and future overrides
        :param language: The language to load the configuration for as a basis for
        the combined configuration
        :return: The combined configuration data as a string
        """
        config = self._calculate_combined_configuration(language)
        return yaml.dump(config)

    def _load_linter_config_file(self, language: str) -> LoadLinterConfigsResult:
        """
        Load any config files for given language if they exist.
        :param language: repo language
        :return:
        """

        # respective name for config file
        language_config_name = Path(f"configs/{slugify(language)}.config.yaml")

        # build absolute path to config file if one exists
        absolute_secureli_path = f'{Path(f"{__file__}").parent.resolve()}'.rsplit(
            "/", 1
        )[0]
        absolute_configs_path = Path(
            f"{absolute_secureli_path}/resources/files/{language_config_name}"
        )

        #  check if config file exists for current language
        if Path.exists(absolute_configs_path):
            language_configs_data = self.data_loader(language_config_name)
            language_configs = yaml.safe_load_all(language_configs_data)

            return LoadLinterConfigsResult(
                successful=True, linter_data=language_configs
            )

        return LoadLinterConfigsResult(successful=False, linter_data=list())

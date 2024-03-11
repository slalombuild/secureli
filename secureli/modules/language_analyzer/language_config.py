from pathlib import Path
from typing import Callable
import yaml

from secureli.modules.shared.models import language
from secureli.modules.shared.resources.slugify import slugify
from secureli.modules.shared.utilities import combine_patterns, hash_config


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

    def get_language_config(
        self, specified_language: str, include_linter: bool
    ) -> language.LanguagePreCommitResult:
        """
        Calculates a hash of the pre-commit file for the given language to be used as part
        of the overall installed configuration.
        :param language: The language specified
        :param include_linter: Whether or not linter pre-commit hooks/configs should be included
        :raises LanguageNotSupportedError if the associated pre-commit file for the language is not found
        :return: LanguagePreCommitConfig - A configuration model containing the language,
        config file data, and a versioning hash of the file contents.
        """
        try:
            config_data = self._calculate_combined_configuration_data(
                specified_language, include_linter
            )
            linter_config_data = (
                self._load_linter_config_file(specified_language)
                if include_linter
                else language.LoadLinterConfigsResult(
                    successful=True, linter_data=list()
                )
            )
            version = hash_config(config_data)
            return language.LanguagePreCommitResult(
                language=specified_language,
                config_data=config_data,
                version=version,
                linter_config=linter_config_data,
            )
        except ValueError:
            raise language.LanguageNotSupportedError(
                f"Language '{specified_language}' is currently unsupported"
            )

    def _calculate_combined_configuration(
        self, specified_language: str, include_linter: bool
    ) -> dict:
        """
        Combine elements of our configuration for the specified language along with
        repo settings like ignored file patterns and pre-commit overrides
        :param language: The language to load the configuration for as a basis for
        the combined configuration
        :param include_linter: Determines whether or not the lint pre-commit repos
        should be added to the configuration result
        :return: The combined configuration data as a dictionary
        """
        config = {"repos": []}
        slugified_language = slugify(specified_language)
        config_folder_names = ["base"]

        if include_linter:
            config_folder_names.append("lint")

        for folder_name in config_folder_names:
            config_data = self.data_loader(
                f"pre-commit/{folder_name}/{slugified_language}-pre-commit.yaml"
            )
            parsed_config = yaml.safe_load(config_data) or {"repos": None}
            repos = parsed_config["repos"]
            config["repos"] += repos or []

        if self.ignored_file_patterns:
            config["exclude"] = combine_patterns(self.ignored_file_patterns)

        return config

    def _calculate_combined_configuration_data(
        self, specified_language: str, include_linter: bool
    ) -> str:
        """
        Combine elements of our configuration for the specified language along with
        repo settings like ignored file patterns and future overrides
        :param language: The language to load the configuration for as a basis for
        the combined configuration
        :param include_linter: Whether or not linter pre-commit hooks should be included
        :return: The combined configuration data as a string
        """
        config = self._calculate_combined_configuration(
            specified_language, include_linter
        )
        return yaml.dump(config)

    def _load_linter_config_file(
        self, specified_language: str
    ) -> language.LoadLinterConfigsResult:
        """
        Load any config files for given language if they exist.
        :param language: repo language
        :return:
        """

        # respective name for config file
        language_config_name = Path(
            f"configs/{slugify(specified_language)}.config.yaml"
        )

        # build absolute path to config file if one exists
        absolute_secureli_path = (
            f'{Path(f"{__file__}").parent.parent.resolve()}'.rsplit("/", 1)[0]
        )
        absolute_configs_path = Path(
            f"{absolute_secureli_path}/modules/shared/resources/files/{language_config_name}"
        )

        #  check if config file exists for current language
        if Path.exists(absolute_configs_path):
            language_configs_data = self.data_loader(language_config_name)
            language_configs = yaml.safe_load_all(language_configs_data)

            return language.LoadLinterConfigsResult(
                successful=True, linter_data=language_configs
            )

        return language.LoadLinterConfigsResult(successful=False, linter_data=list())

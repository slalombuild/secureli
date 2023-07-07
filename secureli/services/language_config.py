from pathlib import Path
from typing import Callable, Optional, Any

import pathspec
import pydantic
import yaml

from secureli.repositories.settings import PreCommitSettings, PreCommitRepo
from secureli.utilities.patterns import combine_patterns
from secureli.resources.slugify import slugify
from secureli.utilities.hash import hash_config


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
        pre_commit_settings: dict[str:Any],
    ):
        self.command_timeout_seconds = command_timeout_seconds
        self.data_loader = data_loader
        self.ignored_file_patterns = ignored_file_patterns
        self.pre_commit_settings = (
            PreCommitSettings.parse_obj(pre_commit_settings)
            if pre_commit_settings
            else PreCommitSettings()
        )

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

        # Combine our .secureli.yaml mutations into the configuration
        self._apply_pre_commit_settings(config)

        return config

    def _find_matching_hook(
        self,
        hook_id: str,
        pre_commit_repo_hooks: dict,
    ) -> Optional[dict]:
        """
        Find a hook from the pre-commit configuration matching the given hook ID
        :param hook_id: The hook ID to find within the repo
        :param pre_commit_repo_hooks: The dictionary representing the repo configuration
        :return: The dictionary representing the hook configuration within the given
        repository, or None if the hook was not present
        """
        matching_pre_commit_hooks = [
            pre_commit_hook
            for pre_commit_hook in pre_commit_repo_hooks
            if pre_commit_hook["id"] == hook_id
        ]
        return matching_pre_commit_hooks[0] if matching_pre_commit_hooks else None

    def _apply_pre_commit_settings(self, config: dict) -> dict:
        """
        Check our pre-commit settings derived from the .secureli.yaml file and merge them
        into our pre-commit configuration, if any
        """
        if "repos" not in config:
            return config

        for pre_commit_repo in config["repos"]:
            repo_url = pre_commit_repo["repo"]

            # If we're suppressing an entire repo, remove it and ignore all other mutations
            if repo_url in self.pre_commit_settings.suppressed_repos:
                config["repos"].remove(pre_commit_repo)
                continue

            matching_settings_repo = self._find_matching_repo_settings(repo_url)

            if not matching_settings_repo:
                continue

            # The hook may have been suppressed within the repo, via .secureli.yaml. Remove it if so.
            self._remove_suppressed_hooks(
                config,
                pre_commit_repo,
                matching_settings_repo,
            )

            pre_commit_repo_hooks = pre_commit_repo["hooks"]

            for hook_settings in matching_settings_repo.hooks or []:
                # Find the hook from the configuration (it may have just been removed)
                matching_hook = self._find_matching_hook(
                    hook_settings.id,
                    pre_commit_repo_hooks,
                )

                if not matching_hook:
                    continue

                # We found a hook in our settings that matches a hook in our config. Update
                # the config with our settings.

                # First we've got arguments to overwrite hook configuration if we supplied overrides
                # Note: this discards any original arguments if present.
                self._override_arguments_if_any(
                    matching_hook,
                    hook_settings.arguments,
                )

                # Second we've got additional arguments to set or append into the hook. This is a good way
                # to go with whatever arguments might be present, but also add additional ones. It would be
                # strange if we specified both `arguments` and `additional_arguments`, but you do you.
                self._apply_additional_args(
                    matching_hook,
                    hook_settings.additional_args,
                )

                # We can also specify file patterns to ignore. Do our usual routine to turn this
                # into a combined pattern we can provide to pre-commit
                self._apply_file_exclusions(
                    matching_hook,
                    hook_settings.exclude_file_patterns,
                )

                # Room to keep supporting more secureli-configurable pre-commit stuff, probably coming soon.

        return config

    def _override_arguments_if_any(
        self,
        pre_commit_hook: dict,
        arguments: Optional[list[str]],
    ):
        """
        Override the hook configuration dictionary with the arguments provided, unless the arguments was None.
        If the arguments were empty, any existing arguments will be removed. If the arguments were None, the
        existing argument configuration will be left unchanged.
        """
        # We may need to wipe out arguments, so we can't use the typical `if not arguments:`
        if arguments is None:
            return

        pre_commit_hook["args"] = arguments

    def _apply_additional_args(
        self,
        pre_commit_hook: dict,
        additional_args: list[str],
    ):
        """
        Append the provided additional arguments into the hook configuration, always preserving
        any existing arguments
        """
        if not additional_args:
            return

        if "args" not in pre_commit_hook:
            pre_commit_hook["args"] = []

        for additional_arg in additional_args:
            pre_commit_hook["args"].append(additional_arg)

    def _apply_file_exclusions(
        self, matching_hook: dict, exclude_file_patterns: Optional[list[str]]
    ):
        """
        Calculate the single regex for the given file exclusion patterns and add to the hook config.
        """
        if not exclude_file_patterns:
            return

        pathspec_lines = pathspec.PathSpec.from_lines(
            pathspec.patterns.GitWildMatchPattern, exclude_file_patterns
        )
        raw_patterns = [
            pathspec_pattern.regex.pattern
            for pathspec_pattern in pathspec_lines.patterns
            if pathspec_pattern.include
        ]
        matching_hook["exclude"] = combine_patterns(raw_patterns)

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

    def _find_matching_repo_settings(self, repo_url: str) -> Optional[PreCommitRepo]:
        """
        Find a repo from our settings that matches the given URL
        :param repo_url: The URL of the repo
        :return: A PreCommitRepo settings object, as managed from .secureli.yaml, or None
        if a match wasn't found.
        """
        matching_settings_repos = [
            repo
            for repo in self.pre_commit_settings.repos
            if repo.url.lower() == repo_url.lower()
        ]
        return matching_settings_repos[0] if matching_settings_repos else None

    def _remove_suppressed_hooks(
        self, config: dict, pre_commit_repo: dict, matching_settings_repo: PreCommitRepo
    ):
        """
        Remove any suppressed hook from the provided repo configuration dictionary completely.
        If the last hook in a repo is removed by this process, the repo itself is removed from
        the configuration completely as well.
        """
        for hook_id in matching_settings_repo.suppressed_hook_ids:
            # This hook is configured by .secureli.yaml to be suppressed, so remove it (and by 'it'
            # I mean any that match the hook's ID, because it's an array)
            matching_repo_hooks = [
                x for x in pre_commit_repo.get("hooks") if x["id"] == hook_id
            ]
            for hook in matching_repo_hooks:
                pre_commit_repo["hooks"].remove(hook)

            # If we removed the last hook from the repo, there's no point to the repo anymore, so remove it.
            if not pre_commit_repo["hooks"] and pre_commit_repo in config["repos"]:
                config["repos"].remove(pre_commit_repo)

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

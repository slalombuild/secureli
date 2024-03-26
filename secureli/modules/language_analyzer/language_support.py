from pathlib import Path
from typing import Callable, Iterable, Optional

import yaml
from secureli.modules.shared.models.config import HookConfiguration, LinterConfig, Repo
from secureli.modules.shared.models import language

import secureli.repositories.secureli_config as SecureliConfig
from secureli.modules.shared.abstractions.pre_commit import PreCommitAbstraction
from secureli.modules.shared.abstractions.echo import EchoAbstraction
from secureli.modules.language_analyzer import git_ignore, language_config
from secureli.modules.shared.utilities import hash_config


class LanguageSupportService:
    """
    Orchestrates a growing list of security best practices for languages. Installs
    them for the provided language.
    """

    def __init__(
        self,
        pre_commit_hook: PreCommitAbstraction,
        language_config: language_config.LanguageConfigService,
        git_ignore: git_ignore.GitIgnoreService,
        data_loader: Callable[[str], str],
        echo: EchoAbstraction,
    ):
        self.git_ignore = git_ignore
        self.pre_commit_hook = pre_commit_hook
        self.language_config = language_config
        self.data_loader = data_loader
        self.echo = echo

    def apply_support(
        self,
        languages: list[str],
        language_config_result: language.BuildConfigResult,
        overwrite_pre_commit: bool,
    ) -> language.LanguageMetadata:
        """
        Applies Secure Build support for the provided languages
        :param languages: list of languages to provide support for
        :param language_config_result: resulting config from language hook detection
        :param overwrite_pre_commit: flag to determine if config should overwrite or append to config file
        :raises LanguageNotSupportedError if support for the language is not provided
        :return: Metadata including version of the language configuration that was just installed
        as well as a secret-detection hook ID, if present.
        """

        path_to_pre_commit_file: Path = (
            self.pre_commit_hook.get_preferred_pre_commit_config_path(
                SecureliConfig.FOLDER_PATH
            )
        )

        linter_config_write_result = self._write_pre_commit_configs(
            language_config_result.linter_configs
        )

        pre_commit_file_mode = "w" if overwrite_pre_commit else "a"
        with open(path_to_pre_commit_file, pre_commit_file_mode) as f:
            data = (
                language_config_result.config_data
                if overwrite_pre_commit
                else language_config_result.config_data["repos"]
            )
            f.write(yaml.dump(data))

        # Add .secureli/ to the gitignore folder if needed
        self.git_ignore.ignore_secureli_files()

        return language.LanguageMetadata(
            version=language_config_result.version,
            security_hook_id=self.secret_detection_hook_id(languages),
            linter_config_write_errors=linter_config_write_result.error_messages,
        )

    def secret_detection_hook_id(self, languages: list[str]) -> Optional[str]:
        """
        Checks the configuration of the provided language to determine if any configured
        hooks are usable for init-time secrets detection. These supported hooks are derived
        from secrets_detecting_repos.yaml in the resources
        :param languages: list of languages to check support for
        :return: The hook ID to use for secrets analysis if supported, otherwise None.
        """
        # lint_languages param can be an empty set since we only need secrets detection hooks
        language_config = self.build_pre_commit_config(languages, [])
        config = language_config.config_data
        secrets_detecting_repos_data = self.data_loader(
            "pre-commit/secrets_detecting_repos.yaml"
        )
        secrets_detecting_repos = yaml.safe_load(secrets_detecting_repos_data)

        # Make sure the repos and configuration don't care about case sensitivity
        all_repos = config.get("repos", [])
        repos = [repo["repo"].lower() for repo in all_repos]
        secrets_detecting_repos = {
            repo.lower(): key for repo, key in secrets_detecting_repos.items()
        }
        secrets_detecting_repos_in_config = [
            repo for repo in repos if repo in secrets_detecting_repos
        ]
        if not secrets_detecting_repos_in_config:
            return None

        # We've identified which repos we have in our configuration that detect secrets. But we
        # don't need the repo, we need the hook ID. And just because we have the repo, doesn't mean we
        # have the hook configured.
        for repo_name in secrets_detecting_repos_in_config:
            repo_config = [
                repo for repo in all_repos if repo["repo"].lower() == repo_name
            ][0]
            repo_hook_ids = [hook["id"] for hook in repo_config.get("hooks", [])]
            secrets_detecting_hooks = [
                hook_id
                for hook_id in repo_hook_ids
                if hook_id in secrets_detecting_repos[repo_name]
            ]
            if secrets_detecting_hooks:
                return secrets_detecting_hooks[0]

        return None

    def get_configuration(self, languages: list[str]) -> HookConfiguration:
        """
        Creates a basic, serializable configuration out of the combined specified language config
        :param languages: list of languages to get config for.
        :return: A serializable Configuration model
        """
        config = self.build_pre_commit_config(languages, set(languages)).config_data

        repos = [self._create_repo(raw_repo) for raw_repo in config.get("repos", [])]
        return HookConfiguration(repos=repos)

    def build_pre_commit_config(
        self,
        languages: list[str],
        lint_languages: Iterable[str],
        pre_commit_config_location: Optional[Path] = None,
    ) -> language.BuildConfigResult:
        """
        Builds the final .pre-commit-config.yaml from all supported repo languages. Also returns any and all
        linter configuration data.
        :param languages: list of languages to get calculated configuration for.
        :param lint_languages: list of languages to add lint pre-commit hooks for.
        :return: language.BuildConfigResult
        """
        config_repos = []
        existing_data = {}
        successful_languages: list[str] = []
        linter_configs: list[LinterConfig] = []
        config_languages = [*languages, "base"]
        config_lint_languages = [*lint_languages, "base"]

        if pre_commit_config_location:
            with open(pre_commit_config_location) as stream:
                try:
                    data = yaml.safe_load(stream)
                    existing_data = data or {}
                    config_repos += data["repos"] if data and data.get("repos") else []

                except yaml.YAMLError:
                    self.echo.error(
                        f"There was an issue parsing existing pre-commit-config.yaml."
                    )
                    return language.BuildConfigResult(
                        successful=False,
                        languages_added=[],
                        config_data={},
                        version="",
                        linter_configs=linter_configs,
                    )

        for config_language in config_languages:
            include_linter = config_language in config_lint_languages
            result = self.language_config.get_language_config(
                config_language, include_linter
            )
            if result.config_data:
                successful_languages.append(config_language)
                (
                    linter_configs.append(
                        LinterConfig(
                            language=config_language,
                            linter_data=result.linter_config.linter_data,
                        )
                    )
                    if result.linter_config.successful
                    else None
                )
                data = yaml.safe_load(result.config_data)
                config_repos += data["repos"] or []

        config = {**existing_data, "repos": config_repos}
        version = hash_config(yaml.dump(config))

        return language.BuildConfigResult(
            successful=True if len(config_repos) > 0 else False,
            languages_added=successful_languages,
            config_data=config,
            version=version,
            linter_configs=linter_configs,
        )

    def _create_repo(self, raw_repo: dict) -> Repo:
        """
        Creates a repository containing pre-commit hooks from a raw dictionary object
        :param raw_repo: dictionary containing repository data.
        :return: repository containing pre-commit hooks
        """
        return Repo(
            repo=raw_repo.get("repo", "unknown"),
            revision=raw_repo.get("rev", "unknown"),
            hooks=[hook.get("id", "unknown") for hook in raw_repo.get("hooks", [])],
        )

    def _write_pre_commit_configs(
        self,
        all_linter_configs: list[LinterConfig],
    ) -> language.LinterConfigWriteResult:
        """
        Install any config files for given language to support any pre-commit commands.
        i.e. Javascript ESLint requires a .eslintrc file to sufficiently use plugins and allow
        for further customization for repo's flavor of Javascript
        :param all_linter_configs: the applicable linter configs to create config files for in the repo
        """

        linter_config_data = [
            (linter_data, config.language)
            for config in all_linter_configs or []
            for linter_data in config.linter_data
        ]

        error_messages: list[str] = []
        successful_languages: list[str] = []

        for config, config_language in linter_config_data:
            try:
                with open(Path(SecureliConfig.FOLDER_PATH / config.filename), "w") as f:
                    f.write(yaml.dump(config.settings))
                    successful_languages.append(config_language)
            except:
                error_messages.append(
                    f"Failed to write {config.filename} linter config file for {config_language}"
                )

        return language.LinterConfigWriteResult(
            successful_languages=successful_languages, error_messages=error_messages
        )

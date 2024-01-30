from pathlib import Path
from typing import Callable, Iterable, Optional, Any

import pydantic
import yaml
from secureli.abstractions.echo import EchoAbstraction

import secureli.repositories.secureli_config as SecureliConfig
from secureli.abstractions.pre_commit import PreCommitAbstraction
from secureli.resources.slugify import slugify
from secureli.services.git_ignore import GitIgnoreService
from secureli.services.language_config import LanguageConfigService
from secureli.utilities.hash import hash_config

supported_languages = [
    "C#",
    "Python",
    "Java",
    "Terraform",
    "TypeScript",
    "JavaScript",
    "Go",
    "Swift",
    "Kotlin",
]


class LanguageMetadata(pydantic.BaseModel):
    version: str
    security_hook_id: Optional[str]
    linter_config_write_errors: Optional[list[str]] = []


class ValidateConfigResult(pydantic.BaseModel):
    """
    The results of calling validate_config
    """

    successful: bool
    output: str


class Repo(pydantic.BaseModel):
    """A repository containing pre-commit hooks"""

    repo: str
    revision: str
    hooks: list[str]


class HookConfiguration(pydantic.BaseModel):
    """A simplified pre-commit configuration representation for logging purposes"""

    repos: list[Repo]


class UnexpectedReposResult(pydantic.BaseModel):
    """
    The result of checking for unexpected repos in config
    """

    missing_repos: Optional[list[str]] = []
    unexpected_repos: Optional[list[str]] = []


class LinterConfigData(pydantic.BaseModel):
    """
    Represents the structure of a linter config file
    """

    filename: str
    settings: Any


class LinterConfig(pydantic.BaseModel):
    language: str
    linter_data: list[LinterConfigData]


class BuildConfigResult(pydantic.BaseModel):
    """Result about building config for all laguages"""

    successful: bool
    languages_added: list[str]
    config_data: dict
    linter_configs: list[LinterConfig]
    version: str


class LinterConfigWriteResult(pydantic.BaseModel):
    """
    Result from writing linter config files
    """

    successful_languages: list[str]
    error_messages: list[str]


class LanguageSupportService:
    """
    Orchestrates a growing list of security best practices for languages. Installs
    them for the provided language.
    """

    def __init__(
        self,
        pre_commit_hook: PreCommitAbstraction,
        language_config: LanguageConfigService,
        git_ignore: GitIgnoreService,
        data_loader: Callable[[str], str],
    ):
        self.git_ignore = git_ignore
        self.pre_commit_hook = pre_commit_hook
        self.language_config = language_config
        self.data_loader = data_loader

    def apply_support(
        self,
        languages: list[str],
        language_config_result: BuildConfigResult,
        overwrite_pre_commit: bool,
    ) -> LanguageMetadata:
        """
        Applies Secure Build support for the provided languages
        :param languages: list of languages to provide support for
        :param language_config_result: resulting config from language hook detection
        :param overwrite_pre_commit: flag to determine if config should overwrite or append to config file
        :raises LanguageNotSupportedError if support for the language is not provided
        :return: Metadata including version of the language configuration that was just installed
        as well as a secret-detection hook ID, if present.
        """

        path_to_pre_commit_file = Path(
            SecureliConfig.FOLDER_PATH / ".pre-commit-config.yaml"
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

        return LanguageMetadata(
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
        language_config = self._build_pre_commit_config(languages, [])
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
        config = self._build_pre_commit_config(languages, set(languages)).config_data

        def create_repo(raw_repo: dict) -> Repo:
            return Repo(
                repo=raw_repo.get("repo", "unknown"),
                revision=raw_repo.get("rev", "unknown"),
                hooks=[hook.get("id", "unknown") for hook in raw_repo.get("hooks", [])],
            )

        repos = [create_repo(raw_repo) for raw_repo in config.get("repos", [])]
        return HookConfiguration(repos=repos)

    def _build_pre_commit_config(
        self, languages: list[str], lint_languages: Iterable[str]
    ) -> BuildConfigResult:
        """
        Builds the final .pre-commit-config.yaml from all supported repo languages. Also returns any and all
        linter configuration data.
        :param languages: list of languages to get calculated configuration for.
        :param lint_languages: list of languages to add lint pre-commit hooks for.
        :return: BuildConfigResult
        """
        config_data = []
        successful_languages: list[str] = []
        linter_configs: list[LinterConfig] = []
        config_languages = [*languages, "base"]
        config_lint_languages = [*lint_languages, "base"]

        for language in config_languages:
            include_linter = language in config_lint_languages
            result = self.language_config.get_language_config(language, include_linter)
            if result.config_data:
                successful_languages.append(language)
                (
                    linter_configs.append(
                        LinterConfig(
                            language=language,
                            linter_data=result.linter_config.linter_data,
                        )
                    )
                    if result.linter_config.successful
                    else None
                )
                data = yaml.safe_load(result.config_data)
                config_data += data["repos"] or []

        config = {"repos": config_data}
        version = hash_config(yaml.dump(config))

        return BuildConfigResult(
            successful=True if len(config_data) > 0 else False,
            languages_added=successful_languages,
            config_data=config,
            version=version,
            linter_configs=linter_configs,
        )

    def _write_pre_commit_configs(
        self,
        all_linter_configs: list[LinterConfig],
    ) -> LinterConfigWriteResult:
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

        for config, language in linter_config_data:
            try:
                with open(Path(SecureliConfig.FOLDER_PATH / config.filename), "w") as f:
                    f.write(yaml.dump(config.settings))
                    successful_languages.append(language)
            except:
                error_messages.append(
                    f"Failed to write {config.filename} linter config file for {language}"
                )

        return LinterConfigWriteResult(
            successful_languages=successful_languages, error_messages=error_messages
        )

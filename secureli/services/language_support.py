from pathlib import Path
from typing import Callable, Optional, Any

import pydantic
import yaml

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
]


class LanguageMetadata(pydantic.BaseModel):
    version: str
    security_hook_id: Optional[str]


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


class LanguageLinterWriteResult(pydantic.BaseModel):
    """Results from installing langauge specific configs for pre-commit hooks"""

    num_successful: int
    num_non_success: int
    non_success_messages: list[str]


class UnexpectedReposResult(pydantic.BaseModel):
    """
    The result of checking for unexpected repos in config
    """

    missing_repos: Optional[list[str]] = []
    unexpected_repos: Optional[list[str]] = []


class LinterConfig(pydantic.BaseModel):
    language: str
    linter_data: list[Any]


class BuildConfigResult(pydantic.BaseModel):
    """Result about building config for all laguages"""

    successful: bool
    languages_added: list[str]
    config_data: dict
    linter_configs: list[LinterConfig]
    version: str


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

    def apply_support(self, languages: list[str]) -> LanguageMetadata:
        """
        Applies Secure Build support for the provided language
        :param languages: list of languages to provide support for
        :raises LanguageNotSupportedError if support for the language is not provided
        :return: Metadata including version of the language configuration that was just installed
        as well as a secret-detection hook ID, if present.
        """

        path_to_pre_commit_file = SecureliConfig.FOLDER_PATH / ".pre-commit-config.yaml"
        # Raises a LanguageNotSupportedError if language doesn't resolve to a yaml file
        language_config_result = self._build_pre_commit_config(languages)

        if len(language_config_result.linter_configs) > 0:
            self._write_pre_commit_configs(language_config_result.linter_configs)

        with open(path_to_pre_commit_file, "w") as f:
            f.write(yaml.dump(language_config_result.config_data))

        # Add .secureli/ to the gitignore folder if needed
        self.git_ignore.ignore_secureli_files()

        return LanguageMetadata(
            version=language_config_result.version,
            security_hook_id=self.secret_detection_hook_id(languages),
        )

    def secret_detection_hook_id(self, languages: list[str]) -> Optional[str]:
        """
        Checks the configuration of the provided language to determine if any configured
        hooks are usable for init-time secrets detection. These supported hooks are derived
        from secrets_detecting_repos.yaml in the resources
        :param languages: list of languages to check support for
        :return: The hook ID to use for secrets analysis if supported, otherwise None.
        """
        language_config = self._build_pre_commit_config(languages)
        config = language_config.config_data
        secrets_detecting_repos_data = self.data_loader("secrets_detecting_repos.yaml")
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
        config = self._build_pre_commit_config(languages).config_data

        def create_repo(raw_repo: dict) -> Repo:
            return Repo(
                repo=raw_repo.get("repo", "unknown"),
                revision=raw_repo.get("rev", "unknown"),
                hooks=[hook.get("id", "unknown") for hook in raw_repo.get("hooks", [])],
            )

        repos = [create_repo(raw_repo) for raw_repo in config.get("repos", [])]
        return HookConfiguration(repos=repos)

    def _build_pre_commit_config(self, languages: list[str]) -> BuildConfigResult:
        """
        Builds the final .pre-commit-config.yaml from all supported repo languages. Also returns any and all
        linter configuration data.
        :param languages: list of languages to get calculated configuration for.
        :return: BuildConfigResult
        """
        config_data = []
        successful_languages = []
        linter_configs: list[LinterConfig] = []

        languages.append("base")

        for language in languages:
            result = self.language_config.get_language_config(language)
            if result.config_data:
                successful_languages.append(language)
                linter_configs.append(
                    LinterConfig(
                        language=language, linter_data=result.linter_config.linter_data
                    )
                ) if result.linter_config.successful else None
                data = yaml.safe_load(result.config_data)
                for config in data["repos"]:
                    config_data.append(config)

        languages.remove("base")
        config = {"repos": config_data}
        version = hash_config(yaml.dump(config))

        return BuildConfigResult(
            successful=True if len(config_data) > 0 else False,
            languages_added=successful_languages,
            config_data=config,
            version=version,
            linter_configs=linter_configs,
        )

    @staticmethod
    def _write_pre_commit_configs(
        all_linter_configs: list[LinterConfig],
    ) -> LanguageLinterWriteResult:
        """
        Install any config files for given language to support any pre-commit commands.
        i.e. Javascript ESLint requires a .eslintrc file to sufficiently use plugins and allow
        for further customization for repo's flavor of Javascript
        :return: LanguageLinterWriteResult
        """

        num_configs_success = 0
        num_configs_non_success = 0
        non_success_messages = list[str]()

        # parse through languages for their linter config if any.
        for language_linter_configs in all_linter_configs:
            # parse though each config for the given language.
            for config in language_linter_configs.linter_data:
                try:
                    config_name = list(config.keys())[0]
                    # generate relative file name and path.
                    config_file_name = f"{slugify(language_linter_configs.language)}.{config_name}.yaml"
                    path_to_config_file = (
                        SecureliConfig.FOLDER_PATH / ".secureli/{config_file_name}"
                    )
                    with open(path_to_config_file, "w") as f:
                        f.write(yaml.dump(config[config_name]))
                    num_configs_success += 1
                except Exception as e:
                    num_configs_non_success += 1
                    non_success_messages.append(f"Unable to install config: {e}")

        return LanguageLinterWriteResult(
            num_successful=num_configs_success,
            num_non_success=num_configs_non_success,
            non_success_messages=non_success_messages,
        )

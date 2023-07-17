from typing import Callable, Optional, Any

import pydantic
import yaml
from pathlib import Path

from secureli.abstractions.pre_commit import PreCommitAbstraction
from secureli.services.git_ignore import GitIgnoreService
from secureli.services.language_config import LanguageConfigService
from secureli.utilities.hash import hash_config
from secureli.resources.slugify import slugify

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

    def version_for_language(self, languages: list[str]) -> str:
        """
        May eventually grow to become a combination of pre-commit hook and other elements
        :param languages: List of languages to determine the version of the current config
        :raises LanguageNotSupportedError if support for the language is not provided
        :return: The version of the current config for the provided language available for install
        """
        # For now, just a passthrough to pre-commit hook abstraction
        return self._build_pre_commit_config(languages).version

    def apply_support(self, languages: list[str]) -> LanguageMetadata:
        """
        Applies Secure Build support for the provided language
        :param languages: list of languages to provide support for
        :raises LanguageNotSupportedError if support for the language is not provided
        :return: Metadata including version of the language configuration that was just installed
        as well as a secret-detection hook ID, if present.
        """

        path_to_pre_commit_file = Path(".pre-commit-config.yaml")

        # Raises a LanguageNotSupportedError if language doesn't resolve to a yaml file
        language_config_result = self._build_pre_commit_config(languages)

        if len(language_config_result.linter_configs) > 0:
            self._write_pre_commit_configs(language_config_result.linter_configs)

        with open(path_to_pre_commit_file, "w") as f:
            f.write(yaml.dump(language_config_result.config_data))

        # Start by identifying and installing the appropriate pre-commit template (if we have one)
        self.pre_commit_hook.install(languages)

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

    def validate_config(self, languages: list[str]) -> ValidateConfigResult:
        """
        Validates that the current configuration matches the expected configuration generated
        by secureli.
        :param language: List of languages to validate against
        :return: Returns a boolean indicating whether the configs match
        """
        current_config = yaml.dump(self.get_current_configuration())
        generated_config = self._build_pre_commit_config(languages)
        current_hash = self.get_current_config_hash()
        expected_hash = generated_config.version
        output = ""

        config_matches = current_hash == expected_hash

        if not config_matches:
            output += "SeCureLI has detected that the .pre-commit-config.yaml file does not match the expected configuration.\n"
            output += "This often occurs when the .pre-commit-config.yaml file has been modified directly.\n"
            output += "All changes to SeCureLI's configuration should be performed through the .secureli.yaml file.\n"
            output += "\n"
            output += self._compare_repo_versions(
                current_config=yaml.safe_load(current_config),
                expected_config=generated_config.config_data,
            )

        return ValidateConfigResult(successful=config_matches, output=output)

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

    def get_current_configuration(self):
        """
        Returns the contents of the .pre-commit-config.yaml file.  Note that this should be used to
        see the current state and not be used for any desired state actions.
        :return: Dictionary containing the contents of the .pre-commit-config.yaml file
        """
        path_to_pre_commit_file = Path(".pre-commit-config.yaml")

        with open(path_to_pre_commit_file, "r") as f:
            data = yaml.safe_load(f)
            return data

    def get_current_config_hash(self) -> str:
        """
        Returns a hash of the current .pre-commit-config.yaml file.  This hash is generated in the
        same way that we generate the version hash for the secureli config file so should be valid
        for comparison.  Note this is the hash of the config file as it currently exists and not
        the hash of the combined config.
        :return: Returns a hash derived from the
        """
        config_data = yaml.dump(self.get_current_configuration())
        config_hash = hash_config(config_data)

        return config_hash

    def _build_pre_commit_config(self, languages: list[str]) -> BuildConfigResult:
        """
        Builds the final .pre-commit-config.yaml from all supported repo languages. Also returns any and all
        linter configuration data.
        :param langauges: list of languages to get calculated configuration for.
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

    def _get_list_of_repo_urls(self, repo_list: list[dict]) -> list[str]:
        """
        Parses a list containing repo dictionaries and returns a list of repo urls
        :param repo_list: List of dictionaries containing repo configurations
        :return: A list of repo urls.
        """
        urls = []

        for repo in repo_list:
            urls.append(repo["repo"])

        return urls

    def _get_dict_with_repo_revs(self, repo_list: list[dict]) -> dict:
        """
        Parses a list containing repo dictionaries and returns a dictionary which
        contains the repo name as the key and rev as the value.
        :param repo_list: List of dictionaries containing repo configurations
        :return: A dict with the repo urls as the key and the repo rev as the value.
        """
        repos_dict = {}

        for repo in repo_list:
            url = repo["repo"]
            rev = repo["rev"]
            repos_dict[url] = rev

        return repos_dict

    def _process_mismatched_repo_versions(
        self, current_repos: list[dict], expected_repos: list[dict]
    ):
        """
        Processes the list of repos from the .pre-commit-config.yaml and the expected (generated) config
        and returns a output as a string which lists any version mismatches detected.
        :param current_repos: List of dictionaries containing repo configurations from the .pre-commit-config.yaml
        file
        :param expected_repos: List of dictionaries containing repo configurations from the expected (generated)
        config
        :return: Returns a string of output representing the version mismatches that were detected
        """
        current_repos_dict = self._get_dict_with_repo_revs(repo_list=current_repos)
        expected_repos_dict = self._get_dict_with_repo_revs(repo_list=expected_repos)
        output = ""

        for repo in expected_repos_dict:
            expected_rev = expected_repos_dict.get(repo)
            current_rev = current_repos_dict.get(repo)
            if expected_rev != current_rev:
                output += (
                    "Expected {} to be rev {} but it is configured to rev {}\n".format(
                        repo, expected_rev, current_rev
                    )
                )

        return output

    def _get_mismatched_repos(self, current_repos: list, expected_repos: list):
        """
        Compares the list of repos in the current config against the list of repos
        in the expected (generated) config and returns an object with a list of missing
        repos and a list of unexpected repos.
        """
        current_repos_set = set(current_repos)
        expected_repos_set = set(expected_repos)
        unexpected_repos = [
            repo for repo in current_repos if repo not in expected_repos_set
        ]
        missing_repos = [
            repo for repo in expected_repos if repo not in current_repos_set
        ]

        return UnexpectedReposResult(
            missing_repos=missing_repos, unexpected_repos=unexpected_repos
        )

    def _process_repo_list_length_mismatch(
        self, current_repos: list[str], expected_repos: list[str]
    ):
        """
        Processes the repo lists for the current config (.pre-commit-config.yaml) and the expected
        (generated) config and generates text output indicating which repos are unexpected and
        which repos are missing.
        :param current_repos: List of repo names that are in the .pre-commit-config.yaml file
        :param expected_repos: List of repo names from the expected (generated) config
        :return: Returns output in string format with the results of the comparison
        """
        output = ""

        mismatch_results = self._get_mismatched_repos(
            current_repos=current_repos,
            expected_repos=expected_repos,
        )
        unexpected_repos = mismatch_results.unexpected_repos
        missing_repos = mismatch_results.missing_repos

        if len(unexpected_repos) > 0:
            output += "Found unexpected repos in .pre-commit-config.yaml:\n"
            for repo in unexpected_repos:
                output += "- {}\n".format(repo)

            output += "\n"

        if len(missing_repos) > 0:
            output += (
                "Some expected repos were misssing from .pre-commit-config.yaml:\n"
            )
            for repo in missing_repos:
                output += "- {}\n".format(repo)

            output += "\n"

        return output

    def _compare_repo_versions(self, current_config: dict, expected_config: dict):
        """
        Compares the current config and expected (generated) config and detemines if there
        are version mismatches for the hooks.
        :param current_config: The current configuration as a dict
        :param expected_config: The expected (generated) configuration as a dict
        :return: Returns a string containing the differences between the two configs.
        """
        current_config_repos = current_config.get("repos", [])
        expected_config_repos = expected_config.get("repos", [])
        output = "Comparing current .pre-commit-config.yaml to expected configuration\n"

        length_of_repos_lists_match = len(current_config_repos) == len(
            expected_config_repos
        )

        if not length_of_repos_lists_match:
            output += self._process_repo_list_length_mismatch(
                current_repos=self._get_list_of_repo_urls(current_config_repos),
                expected_repos=self._get_list_of_repo_urls(expected_config_repos),
            )

        output += self._process_mismatched_repo_versions(
            current_repos=current_config_repos,
            expected_repos=expected_config_repos,
        )

        return output

    def _write_pre_commit_configs(
        self, all_linter_configs: list[LinterConfig]
    ) -> LanguageLinterWriteResult:
        """
        Install any config files for given language to support any pre-commit commands.
        i.e. Javascript ESLint requires a .eslintrc file to sufficiently use plugins and allow
        for further customization for repo's flavor of Javascript
        :param language: repo language
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
                    path_to_config_file = Path(f".secureli/{config_file_name}")

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

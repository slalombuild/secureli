from typing import Optional
import subprocess
import hashlib

import pydantic
import yaml
from pathlib import Path

from secureli.abstractions.pre_commit import PreCommitAbstraction
from secureli.services.git_ignore import GitIgnoreService

supported_languages = [
    "C#",
    "Python",
    "Java",
    "Terraform",
    "TypeScript",
    "JavaScript",
    "Go",
]


class LanguageMetadata(pydantic.BaseModel):
    version: str
    security_hook_id: Optional[str]


class UnexpectedReposResult(pydantic.BaseModel):
    """
    The result of checking for unexpected repos in config
    """

    missing_repos: Optional[list[str]] = []
    unexpected_repos: Optional[list[str]] = []


class ValidateConfigResult(pydantic.BaseModel):
    """
    The results of calling validate_config
    """

    successful: bool
    output: str


class ExecuteResult(pydantic.BaseModel):
    """
    The results of calling execute_hooks
    """

    successful: bool
    output: str


class Repo(pydantic.BaseModel):
    """A repository containing pre-commit hooks"""

    repo: str
    revision: str
    hooks: list[str]


def format_language_output(languages: list[str]) -> str:
    return " ".join(map(str, languages))


class LanguageSupportService:
    """
    Orchestrates a growing list of security best practices for languages. Installs
    them for the provided language.
    """

    def __init__(
        self,
        pre_commit_hook: PreCommitAbstraction,
        git_ignore: GitIgnoreService,
    ):
        self.git_ignore = git_ignore
        self.pre_commit_hook = pre_commit_hook

    def version_for_language(self, languages: list[str]) -> str:
        """
        Calculates a hash of the generated pre-commit file for the given language to be used as part
        of the overall installed configuration.
        :param languages: list of all supported languages to use in config hashing
        :raises LanguageNotSupportedError if the associated pre-commit file for the language is not found
        :return: The hash of the language-pre-commit.yaml file found in the resources
        matching the given language.
        """
        pre_commit_config = self._build_pre_commit_config(languages)
        pre_commit_config_version = self._hash_config(yaml.dump(pre_commit_config))

        return pre_commit_config_version

    def apply_support(self, languages: list[str]) -> LanguageMetadata:
        """
        Applies Secure Build support for the provided languages
        :param languages: list of support languages to supply support for
        :raises LanguageNotSupportedError if support for the language is not provided
        :return: Metadata including version of the language configuration that was just installed
        as well as a secret-detection hook ID, if present.
        """

        path_to_config_file = ".pre-commit-config.yaml"
        pre_commit_config = self._build_pre_commit_config(languages, True)

        with open(path_to_config_file, "w") as f:
            f.write(yaml.dump(pre_commit_config))

        version = self._hash_config(yaml.dump(pre_commit_config))

        return LanguageMetadata(
            version=version, security_hook_id=self.secret_detection_hook_id(languages)
        )

    def secret_detection_hook_id(self, languages: list[str]) -> Optional[str]:
        """
        Checks the configuration of the provided language to determine if any configured
        hooks are usable for init-time secrets detection. These supported hooks are derived
        from secrets_detecting_repos.yaml in the resources
        :param language: The language to check support for
        :return: The hook ID to use for secrets analysis if supported, otherwise None.
        """
        config = self._build_pre_commit_config(languages)

        secrets_detecting_repos = self.pre_commit_hook.get_secret_detecting_repos()

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

    def update(self) -> ExecuteResult:
        """
        Installs the hooks defined in pre-commit-config.yml.
        :return: ExecuteResult, indicating success or failure.
        """
        subprocess_args = ["pre-commit", "install-hooks", "--color", "always"]

        completed_process = subprocess.run(subprocess_args, stdout=subprocess.PIPE)
        output = (
            completed_process.stdout.decode("utf8") if completed_process.stdout else ""
        )
        if completed_process.returncode != 0:
            return ExecuteResult(successful=False, output=output)
        else:
            return ExecuteResult(successful=True, output=output)

    def execute_hooks(
        self, all_files: bool = False, hook_id: Optional[str] = None
    ) -> ExecuteResult:
        """
        Execute the configured hooks against the repository, either against your staged changes
        or all the files in the repo
        :param all_files: True if we want to scan all files, default to false, which only
        scans our staged changes we're about to commit
        :param hook_id: A specific hook to run. If None, all hooks will be run
        :return: ExecuteResult, indicating success or failure.
        """
        # always log colors so that we can print them out later, which does not happen by default
        # when we capture the output (which we do so we can add it to our logs).
        subprocess_args = [
            "pre-commit",
            "run",
            "--color",
            "always",
        ]
        if all_files:
            subprocess_args.append("--all-files")

        if hook_id:
            subprocess_args.append(hook_id)

        completed_process = subprocess.run(subprocess_args, stdout=subprocess.PIPE)
        output = (
            completed_process.stdout.decode("utf8") if completed_process.stdout else ""
        )
        if completed_process.returncode != 0:
            return ExecuteResult(successful=False, output=output)
        else:
            return ExecuteResult(successful=True, output=output)

    def autoupdate_hooks(
        self,
        bleeding_edge: bool = False,
        freeze: bool = False,
        repos: Optional[list] = None,
    ) -> ExecuteResult:
        """
        Updates the precommit hooks but executing precommit's autoupdate command.  Additional info at
        https://pre-commit.com/#pre-commit-autoupdate
        :param bleeding edge: True if updating to the bleeding edge of the default branch instead of
        the latest tagged version (which is the default behavior)
        :param freeze: Set to True to store "frozen" hashes in rev instead of tag names.
        :param repos: List of repos (url as a string) to update. This is used to target specific repos instead of all repos.
        :return: ExecuteResult, indicating success or failure.
        """
        subprocess_args = [
            "pre-commit",
            "autoupdate",
        ]
        if bleeding_edge:
            subprocess_args.append("--bleeding-edge")

        if freeze:
            subprocess_args.append("--freeze")

        if repos:
            repo_args = []

            if isinstance(repos, str):
                # If a string is passed in, converts to a list containing the string
                repos = [repos]

            for repo in repos:
                if isinstance(repo, str):
                    arg = "--repo {}".format(repo)
                    repo_args.append(arg)
                else:
                    output = "Unable to update repo, string validation failed. Repo parameter should be a dictionary of strings."
                    return ExecuteResult(successful=False, output=output)

            subprocess_args.extend(repo_args)

        completed_process = subprocess.run(subprocess_args, stdout=subprocess.PIPE)
        output = (
            completed_process.stdout.decode("utf8") if completed_process.stdout else ""
        )
        if completed_process.returncode != 0:
            return ExecuteResult(successful=False, output=output)
        else:
            return ExecuteResult(successful=True, output=output)

    def remove_unused_hooks(self) -> ExecuteResult:
        """
        Removes unused hook repos from the cache.  Pre-commit determines which flags are "unused" by comparing
        the repos to the pre-commit-config.yaml file.  Any cached hook repos that are not in the config file
        will be removed from the cache.
        :return: ExecuteResult, indicating success or failure.
        """
        subprocess_args = ["pre-commit", "gc", "--color", "always"]

        completed_process = subprocess.run(subprocess_args, stdout=subprocess.PIPE)
        output = (
            completed_process.stdout.decode("utf8") if completed_process.stdout else ""
        )
        if completed_process.returncode != 0:
            return ExecuteResult(successful=False, output=output)
        else:
            return ExecuteResult(successful=True, output=output)

    def get_current_config_hash(self) -> str:
        """
        Returns a hash of the current .pre-commit-config.yaml file.  This hash is generated in the
        same way that we generate the version hash for the secureli config file so should be valid
        for comparison.  Note this is the hash of the config file as it currently exists and not
        the hash of the combined config.
        :return: Returns a hash derived from the
        """
        config_data = yaml.dump(self._get_current_configuration())
        config_hash = self._hash_config(config_data)

        return config_hash

    def validate_config(self, languages: list[str]) -> bool:
        """
        Validates that the current configuration matches the expected configuration generated
        by secureli.
        :param language: The language to validate against
        :return: Returns a boolean indicating whether the configs match
        """
        current_config = yaml.dump(self._get_current_configuration())

        # TODO generate from all languages
        generated_config = yaml.dump(self._build_pre_commit_config(languages))
        current_hash = self.get_current_config_hash()
        expected_hash = self._hash_config(generated_config)
        output = ""

        config_matches = current_hash == expected_hash

        if not config_matches:
            output += "SeCureLI has detected that the .pre-commit-config.yaml file does not match the expected configuration.\n"
            output += "This often occurs when the .pre-commit-config.yaml file has been modified directly.\n"
            output += "All changes to SeCureLI's configuration should be performed through the .secureli.yaml file.\n"
            output += "\n"
            output += self._compare_repo_versions(
                current_config=yaml.safe_load(current_config),
                expected_config=yaml.safe_load(generated_config),
            )

        return ValidateConfigResult(successful=config_matches, output=output)

    def get_serialized_config(self, languages: list[str]):
        configs = []

        for language in languages:
            configs.append(self.pre_commit_hook.get_serialized_configuration(language))

        return configs

    def _get_current_configuration(self):
        """
        Returns the contents of the .pre-commit-config.yaml file.  Note that this should be used to
        see the current state and not be used for any desired state actions.
        :return: Dictionary containing the contents of the .pre-commit-config.yaml file
        """
        path_to_pre_commit_file = Path(".pre-commit-config.yaml")

        with open(path_to_pre_commit_file, "r") as f:
            data = yaml.safe_load(f)
            return data

    def _build_pre_commit_config(self, languages: list[str], install=False):
        all_configs = []

        languages.append("base")

        for language in languages:
            result = self.pre_commit_hook.get_configuration(language, install)
            if result.successful:
                for config in result.config_data["repos"]:
                    all_configs.append(config)

        languages.remove("base")

        return {"repos": all_configs}

    def _hash_config(self, config: str) -> str:
        """
        Creates an MD5 hash from a config string
        :return: A hash string
        """
        config_hash = hashlib.md5(
            config.encode("utf8"), usedforsecurity=False
        ).hexdigest()

        return config_hash

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
            if "rev" in repo.keys():
                rev = repo["rev"]
                repos_dict[url] = rev
            else:
                repos_dict[url] = ""

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

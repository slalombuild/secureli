from typing import Optional

import pydantic

from secureli.abstractions.pre_commit import PreCommitAbstraction
from secureli.services.git_ignore import GitIgnoreService

supported_languages = ["C#", "Python", "Java", "Terraform", "TypeScript"]


class LanguageMetadata(pydantic.BaseModel):
    version: str
    security_hook_id: Optional[str]


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

    def version_for_language(self, language: str) -> str:
        """
        May eventually grow to become a combination of pre-commit hook and other elements
        :param language: The language to determine the version of the current config
        :raises LanguageNotSupportedError if support for the language is not provided
        :return: The version of the current config for the provided language available for install
        """
        # For now, just a passthrough to pre-commit hook abstraction
        return self.pre_commit_hook.version_for_language(language)

    def apply_support(self, language: str) -> LanguageMetadata:
        """
        Applies Secure Build support for the provided language
        :param language: The language to provide support for
        :raises LanguageNotSupportedError if support for the language is not provided
        :return: Metadata including version of the language configuration that was just installed
        as well as a secret-detection hook ID, if present.
        """

        # Start by identifying and installing the appropriate pre-commit template (if we have one)
        install_result = self.pre_commit_hook.install(language)

        # Add .secureli/ to the gitignore folder if needed
        self.git_ignore.ignore_secureli_files()

        return LanguageMetadata(
            version=install_result.version_installed,
            security_hook_id=self.pre_commit_hook.secret_detection_hook_id(language),
        )

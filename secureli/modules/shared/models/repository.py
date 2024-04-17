from enum import Enum
from typing import Optional
from pydantic import BaseModel, BaseSettings, Field
from secureli.modules.shared.consts.repository import default_ignored_extensions
from secureli.modules.shared.models.echo import Level
from secureli.modules.shared.models.language import LanguageSupportSettings


class RepoFilesSettings(BaseSettings):
    """
    Settings that adjust how seCureLI evaluates the consuming repository.
    """

    max_file_size: int = Field(default=100000)
    ignored_file_extensions: list[str] = Field(default=default_ignored_extensions)
    exclude_file_patterns: list[str] = Field(default=[])


class EchoSettings(BaseSettings):
    """
    Settings that affect how seCureLI provides information to the user.
    """

    level: Level = Field(default=Level.warn)


class TelemetrySettings(BaseSettings):
    """
    Settings for telemetry/logging i.e. New Relic logs
    """

    api_url: Optional[str] = None


class PreCommitHook(BaseModel):
    """
    Hook settings for pre-commit.
    """

    id: str
    arguments: Optional[list[str]] = Field(default=[])
    additional_args: Optional[list[str]] = Field(default=[])
    exclude_file_patterns: Optional[list[str]] = Field(default=[])


class PreCommitRepo(BaseModel):
    """
    Repo settings for pre-commit.
    """

    url: str = Field(alias="repo")
    rev: str
    hooks: list[PreCommitHook] = Field(default=[])
    suppressed_hook_ids: list[str] = Field(default=[])


class PreCommitSettings(BaseModel):
    """
    Various adjustments that affect how seCureLI configures the pre-commit system.

    Extends schema for .pre-commit-config.yaml file.
    See for details: https://pre-commit.com/#pre-commit-configyaml---top-level

    """

    repos: list[PreCommitRepo] = Field(default=[])
    suppressed_repos: list[str] = Field(default=[])


class SecureliFile(BaseModel):
    """
    Represents the contents of the .secureli.yaml file
    """

    repo_files: Optional[RepoFilesSettings] = None
    echo: Optional[EchoSettings] = None
    language_support: Optional[LanguageSupportSettings] = Field(default=None)
    telemetry: Optional[TelemetrySettings] = None


class SecureliConfig(BaseModel):
    languages: Optional[list[str]] = None
    version_installed: Optional[str] = None
    last_hook_update_check: Optional[int] = 0


class DeprecatedSecureliConfig(BaseModel):
    """
    Represents a model containing all current and past options for repo-config.yaml
    """

    overall_language: Optional[str]
    version_installed: Optional[str]


class VerifyConfigOutcome(str, Enum):
    UP_TO_DATE = ("up-to-date",)
    OUT_OF_DATE = ("out-of-date",)
    MISSING = "missing"

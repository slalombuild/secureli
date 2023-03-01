from enum import Enum
from pathlib import Path
from typing import Any, Optional

import pydantic
import yaml
from pydantic import Field


default_ignored_extensions = [
    # Images
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".bmp",
    ".tiff",
    "psd",
    # Videos
    ".mp4",
    ".mkv",
    ".avi",
    ".mov",
    ".mpg",
    ".vob",
    # Audio
    ".mp3",
    ".aac",
    ".wav",
    ".flac",
    ".ogg",
    ".mka",
    ".wma",
    # Documents
    ".pdf",
    ".doc",
    ".xls",
    ".ppt",
    ".docx",
    ".odt",
    ".drawio",
    # Archives
    ".zip",
    ".rar",
    ".7z",
    ".tar",
    ".iso",
    # Databases
    ".mdb",
    ".accde",
    ".frm",
    ".sqlite",
    # Executable
    ".exe",
    ".dll",
    ".so",
    ".class",
    # Other
    ".pyc",
]


class RepoFilesSettings(pydantic.BaseSettings):
    """
    Settings that adjust how SeCureLI evaluates the consuming repository.
    """

    max_file_size: int = Field(default=100000)
    ignored_file_extensions: list[str] = Field(default=default_ignored_extensions)
    exclude_file_patterns: list[str] = Field(default=[])


class EchoLevel(str, Enum):
    debug = "DEBUG"
    info = "INFO"
    warn = "WARN"
    error = "ERROR"


class EchoSettings(pydantic.BaseSettings):
    """
    Settings that affect how SeCureLI provides information to the user.
    """

    level: EchoLevel = Field(default=EchoLevel.error)


class LanguageSupportSettings(pydantic.BaseSettings):
    """
    Settings that affect how SeCureLI performs language analysis and support.
    """

    command_timeout_seconds: int = Field(default=300)


class PreCommitHook(pydantic.BaseSettings):
    """
    Hook settings for pre-commit.
    """

    id: str
    arguments: Optional[list[str]] = Field(default=None)
    additional_args: Optional[list[str]] = Field(default=None)
    exclude_file_patterns: Optional[list[str]] = Field(default=None)


class PreCommitRepo(pydantic.BaseSettings):
    """
    Repo settings for pre-commit.
    """

    url: str
    hooks: list[PreCommitHook] = Field(default=[])
    suppressed_hook_ids: list[str] = Field(default=[])


class PreCommitSettings(pydantic.BaseSettings):
    """
    Various adjustments that affect how SeCureLI configures the pre-commit system.
    """

    repos: list[PreCommitRepo] = Field(default=[])
    suppressed_repos: list[str] = Field(default=[])


def secureli_yaml_settings(
    settings: pydantic.BaseSettings,
) -> dict[str, Any]:
    """
    Loads the .secureli.yaml file as the source for settings.
    """

    encoding = settings.__config__.env_file_encoding
    path_to_settings = Path(".secureli.yaml")
    if not path_to_settings.exists():
        return {}
    with open(
        path_to_settings,
        "r",
        encoding=encoding,
    ) as f:
        data = yaml.safe_load(f)
        return data


class Settings(pydantic.BaseSettings):
    """
    The settings loaded from a collection of data sources, but most notably
    the .secureli.yaml file.
    """

    repo_files: RepoFilesSettings = RepoFilesSettings()
    echo: EchoSettings = EchoSettings()
    language_support: LanguageSupportSettings = LanguageSupportSettings()
    pre_commit: PreCommitSettings = PreCommitSettings()

    class Config:
        env_file_encoding = "utf-8"

        @classmethod
        def customise_sources(
            cls,
            init_settings,
            env_settings,
            file_secret_settings,
        ):
            return (
                init_settings,
                secureli_yaml_settings,
                env_settings,
                file_secret_settings,
            )

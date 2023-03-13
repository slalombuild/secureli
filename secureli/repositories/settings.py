from pathlib import Path
from typing import Optional, Literal
from enum import Enum
import yaml

from pydantic import BaseModel, BaseSettings, Field


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


class RepoFilesSettings(BaseSettings):
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


class EchoSettings(BaseSettings):
    """
    Settings that affect how SeCureLI provides information to the user.
    """

    level: EchoLevel = Field(default=EchoLevel.error)


class LanguageSupportSettings(BaseSettings):
    """
    Settings that affect how SeCureLI performs language analysis and support.
    """

    command_timeout_seconds: int = Field(default=300)


class PreCommitHook(BaseSettings):
    """
    Hook settings for pre-commit.
    """

    id: str
    arguments: Optional[list[str]] = Field(default=None)
    additional_args: Optional[list[str]] = Field(default=None)
    exclude_file_patterns: Optional[list[str]] = Field(default=None)


class PreCommitRepo(BaseSettings):
    """
    Repo settings for pre-commit.
    """

    url: str
    hooks: list[PreCommitHook] = Field(default=[])
    suppressed_hook_ids: list[str] = Field(default=[])


class PreCommitSettings(BaseSettings):
    """
    Various adjustments that affect how SeCureLI configures the pre-commit system.
    """

    repos: list[PreCommitRepo] = Field(default=[])
    suppressed_repos: list[str] = Field(default=[])


class SecureliFile(BaseModel):
    """
    Represents the contents of the .secureli file
    """

    repo_files: Optional[RepoFilesSettings]
    echo: Optional[EchoSettings]
    language_support: Optional[LanguageSupportSettings]
    pre_commit: Optional[PreCommitSettings]


class SecureliRepository:
    """ """

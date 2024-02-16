from pathlib import Path
from typing import Optional
from pydantic import BaseModel, BaseSettings, Field
from secureli.utilities.logging import EchoLevel

import yaml


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
    Settings that adjust how seCureLI evaluates the consuming repository.
    """

    max_file_size: int = Field(default=100000)
    ignored_file_extensions: list[str] = Field(default=default_ignored_extensions)
    exclude_file_patterns: list[str] = Field(default=[])


class EchoSettings(BaseSettings):
    """
    Settings that affect how seCureLI provides information to the user.
    """

    level: EchoLevel = Field(default=EchoLevel.warn)


class LanguageSupportSettings(BaseSettings):
    """
    Settings that affect how seCureLI performs language analysis and support.
    """

    command_timeout_seconds: int = Field(default=300)


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


class SecureliRepository:
    """
    Represents the .secureli.yaml file in the root directory.  Saves and loads data from the file.
    """

    def __init__(self):
        self.secureli_file_path = Path(".") / ".secureli.yaml"

    def save(self, settings: SecureliFile):
        """
        Saves changes to the settings file
        :param settings: The populated settings file to save
        """
        # Removes empty keys to prevent type errors
        settings_dict = {
            key: value for (key, value) in settings.dict().items() if value is not None
        }

        # Converts EchoLevel to string
        if settings_dict.get("echo"):
            settings_dict["echo"]["level"] = "{}".format(settings_dict["echo"]["level"])

        with open(self.secureli_file_path, "w") as f:
            yaml.dump(settings_dict, f)

    def load(self, folder_path: Path) -> SecureliFile:
        """
        Reads the contents of the .secureli.yaml file and returns it
        :return: SecureliFile containing the contents of the settings file
        """
        self.secureli_file_path = folder_path / ".secureli.yaml"
        if not self.secureli_file_path.exists():
            return SecureliFile()

        with open(self.secureli_file_path, "r") as f:
            data = yaml.safe_load(f)
            return SecureliFile.parse_obj(data)

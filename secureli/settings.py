from pathlib import Path
from typing import Any

import pydantic
import yaml

import secureli.repositories.secureli_config as SecureliConfig
from secureli.repositories.settings import (
    RepoFilesSettings,
    EchoSettings,
    LanguageSupportSettings,
)


def secureli_yaml_settings(
    settings: pydantic.BaseSettings,
) -> dict[str, Any]:
    """
    Loads the .secureli.yaml file as the source for settings.
    """

    encoding = settings.__config__.env_file_encoding
    path_to_settings = Path(SecureliConfig.FOLDER_PATH / ".secureli.yaml")
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

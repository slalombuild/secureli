from pathlib import Path
from typing import Any, Optional

import pydantic
import yaml

from secureli.repositories.settings import (
    RepoFilesSettings,
    EchoSettings,
    LanguageSupportSettings,
    PreCommitSettings,
)


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

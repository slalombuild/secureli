from pathlib import Path
from typing import Optional
from enum import Enum
import yaml

from pydantic import BaseModel


class SecureliConfig(BaseModel):
    languages: Optional[list[str]]
    version_installed: Optional[str]


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


class SecureliConfigRepository:
    """Save and retrieve the SeCureLI configuration"""

    def save(self, secureli_config: SecureliConfig):
        """
        Save the specified configuration to the .secureli folder
        :param secureli_config: The populated configuration to save
        """
        secureli_folder_path = self._initialize_secureli_directory()
        secureli_config_path = secureli_folder_path / "repo-config.yaml"
        with open(secureli_config_path, "w") as f:
            yaml.dump(secureli_config.dict(), f)

    def load(self) -> SecureliConfig:
        """
        Load the SeCureLI config from the expected configuration file path or return a new
        configuration object, capable of being modified and saved via the `save` method
        """
        secureli_folder_path = self._initialize_secureli_directory()
        secureli_config_path = secureli_folder_path / "repo-config.yaml"
        if not secureli_config_path.exists():
            return SecureliConfig()

        with open(secureli_config_path, "r") as f:
            data = yaml.safe_load(f)
            return SecureliConfig.parse_obj(data)

    def verify(self) -> VerifyConfigOutcome:
        """
        Check secureli config and verify that it matches most current schema.
        """
        secureli_folder_path = self._initialize_secureli_directory()
        secureli_config_path = secureli_folder_path / "repo-config.yaml"
        if not secureli_config_path.exists():
            return VerifyConfigOutcome.MISSING

        with open(secureli_config_path, "r") as f:
            current_data = yaml.safe_load(f)

        expected_config_schema = SecureliConfig.schema()

        expected_keys = []

        for key in expected_config_schema["properties"]:
            expected_keys.append(key)

        for key in current_data:
            if key not in expected_keys:
                return VerifyConfigOutcome.OUT_OF_DATE

        return VerifyConfigOutcome.UP_TO_DATE

    def update(self) -> SecureliConfig:
        """
        Update any older config version to match most current config.
        """
        secureli_folder_path = self._initialize_secureli_directory()
        secureli_config_path = secureli_folder_path / "repo-config.yaml"
        if not secureli_config_path.exists():
            return SecureliConfig()

        with open(secureli_config_path, "r") as f:
            data = yaml.safe_load(f)
            old_config = DeprecatedSecureliConfig.parse_obj(data)

        return SecureliConfig(
            languages=[old_config.overall_language],
            version_installed=old_config.version_installed,
        )

    def _initialize_secureli_directory(self):
        """
        Creates the .secureli folder within the current directory if needed.
        :return: The folder path of the .secureli folder that either exists or was just created.
        """
        secureli_folder_path = Path(".") / ".secureli"
        secureli_folder_path.mkdir(parents=True, exist_ok=True)
        return secureli_folder_path

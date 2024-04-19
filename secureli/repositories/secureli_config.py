from pathlib import Path

import yaml

import secureli.modules.shared.models.config as config

FOLDER_PATH = Path(".")


class SecureliConfigRepository:
    """Save and retrieve the seCureLI configuration"""

    def save(self, secureli_config: config.SecureliConfig):
        """
        Save the specified configuration to the .secureli folder
        :param secureli_config: The populated configuration to save
        """
        secureli_folder_path = self._initialize_secureli_directory()
        secureli_config_path = secureli_folder_path / "repo-config.yaml"
        with open(secureli_config_path, "w") as f:
            yaml.dump(secureli_config.dict(), f)

    def load(self) -> config.SecureliConfig:
        """
        Load the seCureLI config from the expected configuration file path or return a new
        configuration object, capable of being modified and saved via the `save` method
        """
        secureli_folder_path = self._initialize_secureli_directory()
        secureli_config_path = secureli_folder_path / "repo-config.yaml"

        if not secureli_config_path.exists():
            return config.SecureliConfig()

        with open(secureli_config_path, "r") as f:
            data = yaml.safe_load(f)
            return config.SecureliConfig.parse_obj(data)

    def verify(self) -> config.VerifyConfigOutcome:
        """
        Check secureli config and verify that it matches most current schema.
        """
        secureli_folder_path = self._initialize_secureli_directory()
        secureli_config_path = secureli_folder_path / "repo-config.yaml"
        if not secureli_config_path.exists():
            return config.VerifyConfigOutcome.MISSING

        with open(secureli_config_path, "r") as f:
            current_data = yaml.safe_load(f)

        expected_config_schema = config.SecureliConfig.schema()

        expected_keys = []

        for key in expected_config_schema["properties"]:
            expected_keys.append(key)

        for key in current_data:
            if key not in expected_keys:
                return config.VerifyConfigOutcome.OUT_OF_DATE

        return config.VerifyConfigOutcome.UP_TO_DATE

    def update(self) -> config.SecureliConfig:
        """
        Update any older config version to match most current config.
        """
        secureli_folder_path = self._initialize_secureli_directory()
        secureli_config_path = secureli_folder_path / "repo-config.yaml"
        if not secureli_config_path.exists():
            return config.SecureliConfig()

        with open(secureli_config_path, "r") as f:
            data = yaml.safe_load(f)
            old_config = config.DeprecatedSecureliConfig.parse_obj(data)
        languages: list[str] | None = (
            [old_config.overall_language] if old_config.overall_language else None
        )

        return config.SecureliConfig(
            languages=languages,
            version_installed=old_config.version_installed,
        )

    def _initialize_secureli_directory(self):
        """
        Creates the .secureli folder within the current directory if needed.
        :return: The folder path of the .secureli folder that either exists or was just created.
        """

        secureli_folder_path = Path(FOLDER_PATH) / ".secureli"
        secureli_folder_path.mkdir(parents=True, exist_ok=True)
        return secureli_folder_path

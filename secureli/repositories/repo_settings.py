from pathlib import Path

import yaml

from secureli.modules.shared.models.repository import SecureliFile


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

        # Converts echo Level to string
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

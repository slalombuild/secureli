from pathlib import Path
import re

from secureli.utilities.patterns import combine_patterns


class RepoFilesRepository:
    """
    Loads files in a given repository, or raises ValueError if the provided path is not a git repo
    """

    def __init__(
        self,
        max_file_size: int,
        ignored_file_extensions: str,
        ignored_file_patterns: list[str],
    ):
        self.max_file_size = max_file_size
        self.ignored_file_extensions = ignored_file_extensions
        self.ignored_file_patterns = ignored_file_patterns

    def list_repo_files(self, folder_path: Path) -> list[Path]:
        """
        Loads visible files in a given repository, or raises ValueError if the provided path is not a git repo
        :param folder_path: The path to a git repo containing files
        :raises ValueError: The specified path does not exist or is not a git repo
        :return: The visible files within the specified repo as a list of Path objects
        """
        git_path = folder_path / ".git"
        if not git_path.exists() or not git_path.is_dir():
            raise ValueError("The current folder is not a Git repository!")

        file_paths = [
            f
            for f in list(folder_path.rglob("*.*"))
            if f.is_file()
            and self._no_part_is_invisible(f)
            and self._file_extension_not_ignored(f)
            and self._file_is_not_ignored(f)
        ]
        return file_paths

    def _file_is_not_ignored(self, file_path: Path):
        """
        True if the file does not match on patterns within secureliignore or gitignore
        :param file_path: The file in question
        :return: True if the file is not ignored, otherwise False
        """

        combined_ignore_pattern = combine_patterns(self.ignored_file_patterns)
        return not combined_ignore_pattern or not re.findall(
            combined_ignore_pattern, str(file_path)
        )

    def _file_extension_not_ignored(self, file_path: Path):
        """
        True if the file's extension isn't ignored by secureli
        :param file_path: The file in question
        :return: True if the file's extension isn't ignored by secureli, otherwise False
        """
        return file_path.suffix not in self.ignored_file_extensions

    def _no_part_is_invisible(self, file_path: Path):
        """
        True if the file itself and any of its folders respective to the working
        directory are visible
        :param file_path: The file in question
        :return: True if the file itself and any of its folders respective to the
        working directory are visible. Otherwise False
        """
        return not [p for p in file_path.parts if p[0] == "."]

    def load_file(self, file_path: Path) -> str:
        """
        Loads the contents of the specified file into memory or raises a ValueError
        :param file_path: The path to the file to load
        :raises A ValueError if an error occurs loading the file
        :return: the contents of the file as a str, or raises a ValueError
        """

        if not file_path.exists() or not file_path.is_file():
            raise ValueError(f"File at path {file_path} did not exist")

        if file_path.stat().st_size > self.max_file_size:
            raise ValueError(f"File at path {file_path} was too big to scan")

        try:
            with open(file_path, "r", encoding="utf8") as file_handle:
                text = file_handle.read()
                return text
        except IOError:
            pass
        except ValueError:
            pass

        raise ValueError(f"An unknown error occurred loading the file from {file_path}")

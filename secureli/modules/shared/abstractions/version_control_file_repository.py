from abc import ABC, abstractmethod
from pathlib import Path


class VersionControlFileRepositoryAbstraction(ABC):
    """
    Abstracts common version control repository functions
    """

    @abstractmethod
    def list_repo_files(self, folder_path: Path) -> list[Path]:
        pass

    @abstractmethod
    def list_staged_files(self, folder_path: Path) -> list[Path]:
        pass

    @abstractmethod
    def load_file(self, file_path: Path) -> str:
        pass

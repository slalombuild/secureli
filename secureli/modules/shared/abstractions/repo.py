from abc import ABC, abstractmethod
import git


class RepoAbstraction(ABC):
    """
    Abstracts the configuring and execution of git repo features.
    """

    @abstractmethod
    def get_commit_diff(self) -> list[str]:
        pass


class GitRepo(RepoAbstraction):
    """
    Implementation and wrapper around git repo features
    """

    def get_commit_diff(self) -> list[str]:
        repo = git.Repo()
        try:
            return repo.head.commit.diff()
        except:
            return []

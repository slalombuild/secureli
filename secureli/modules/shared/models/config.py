from typing import Any
import pydantic


class Repo(pydantic.BaseModel):
    """A repository containing pre-commit hooks"""

    repo: str
    revision: str
    hooks: list[str]


class HookConfiguration(pydantic.BaseModel):
    """A simplified pre-commit configuration representation for logging purposes"""

    repos: list[Repo]


class LinterConfigData(pydantic.BaseModel):
    """
    Represents the structure of a linter config file
    """

    filename: str
    settings: Any


class LinterConfig(pydantic.BaseModel):
    language: str
    linter_data: list[LinterConfigData]

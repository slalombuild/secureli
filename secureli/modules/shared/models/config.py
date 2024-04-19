from enum import Enum
from typing import Any, Optional
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


class SecureliConfig(pydantic.BaseModel):
    languages: Optional[list[str]] = None
    version_installed: Optional[str] = None
    last_hook_update_check: Optional[int] = 0


class DeprecatedSecureliConfig(pydantic.BaseModel):
    """
    Represents a model containing all current and past options for repo-config.yaml
    """

    overall_language: Optional[str]
    version_installed: Optional[str]


class VerifyConfigOutcome(str, Enum):
    UP_TO_DATE = ("up-to-date",)
    OUT_OF_DATE = ("out-of-date",)
    MISSING = "missing"

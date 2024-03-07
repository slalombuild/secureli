from pathlib import Path
from typing import Any, Optional
import pydantic

from secureli.modules.shared.models.config import LinterConfig


class SkippedFile(pydantic.BaseModel):
    """
    A file skipped by the analysis phase.
    """

    file_path: Path
    error_message: str


class AnalyzeResult(pydantic.BaseModel):
    """
    The result of the analysis phase.
    """

    language_proportions: dict[str, float]
    skipped_files: list[SkippedFile]


class LanguageNotSupportedError(Exception):
    """The given language was not supported by the PreCommitHooks abstraction"""

    pass


class LoadLinterConfigsResult(pydantic.BaseModel):
    """Results from finding and loading any pre-commit configs for the language"""

    successful: bool
    linter_data: list[Any]


class LanguagePreCommitResult(pydantic.BaseModel):
    """
    A configuration model for a supported pre-commit-configurable language.
    """

    language: str
    config_data: str
    version: str
    linter_config: LoadLinterConfigsResult


class LanguageMetadata(pydantic.BaseModel):
    version: str
    security_hook_id: Optional[str]
    linter_config_write_errors: Optional[list[str]] = []

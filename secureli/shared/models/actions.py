from enum import Enum
from typing import Optional

import pydantic

from secureli.repositories.secureli_config import SecureliConfig
from secureli.services.language_analyzer import AnalyzeResult


class VerifyOutcome(str, Enum):
    INSTALL_CANCELED = "install-canceled"
    INSTALL_FAILED = "install-failed"
    INSTALL_SUCCEEDED = "install-succeeded"
    UPDATE_CANCELED = "update-canceled"
    UPDATE_SUCCEEDED = "update-succeeded"
    UPDATE_FAILED = "update-failed"
    UP_TO_DATE = "up-to-date"


class VerifyResult(pydantic.BaseModel):
    """
    The outcomes of performing verification. Actions can use these results
    to decide whether to proceed with their post-initialization actions or not.
    """

    outcome: VerifyOutcome
    config: Optional[SecureliConfig] = None
    analyze_result: Optional[AnalyzeResult] = None

from dataclasses import dataclass
from enum import Enum

from secureli.models.result import Result


class PublishResultsOption(Enum):
    ALWAYS = "always"
    NEVER = "never"
    ON_FAIL = "on-fail"


@dataclass
class PublishLogResult:
    result: Result
    result_message: str

from enum import Enum


class ExitCode(Enum):
    SCAN_ISSUES_DETECTED = 3
    PII_SCAN_ISSUES_DETECTED = 4
    TYPE_ERROR = 5
    NAME_ERROR = 6
    VALIDATION_ERROR = 7
    CONFIG_ERROR = 8
    DICT_ERROR = 9
    MISSING_ERROR = 10

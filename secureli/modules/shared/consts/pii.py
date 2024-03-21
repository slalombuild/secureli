from enum import Enum

PII_CHECK = {
    "Email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b",
    "Social security number": r"(?!000|666|333)0*(?:[0-6][0-9][0-9]|[0-7][0-6][0-9]|[0-7][0-7][0-2])[- ](?!00)[0-9]{2}[- ](?!0000)[0-9]{4}",
    "Phone number": r"[\+]?[(]?[0-9]{3}[)]?[-\s\.]?[0-9]{3}[-\s\.]?[0-9]{4,6}",
}

IGNORED_EXTENSIONS = [
    ".md",
    ".lock",
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".svg",
    ".ico",
    ".eot",
    ".ttf",
    ".woff",
    ".css",
]

SECURELI_GITHUB = "https://github.com/slalombuild/secureli"


class Format(str, Enum):
    """
    Enum to use for formatting PII results
    """

    PURPLE_TXT = "purple_text"
    RED_TXT = "red_text"
    RED_BG = "red_background"
    GREEN_BG = "green_background"
    DEFAULT = "default_format"
    BOLD_WEIGHT = "bold_weight"
    REG_WEIGHT = "regular_weight"


RESULT_FORMAT = {
    Format.DEFAULT: "\033[m",
    Format.PURPLE_TXT: "\033[35m",
    Format.RED_TXT: "\033[31m",
    Format.GREEN_BG: "\033[42m",
    Format.RED_BG: "\033[41m",
    Format.BOLD_WEIGHT: "\033[1m",
    Format.REG_WEIGHT: "\033[22m",
}

DISABLE_PII_MARKER = "disable-pii-scan"

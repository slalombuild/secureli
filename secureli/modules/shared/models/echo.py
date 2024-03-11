from enum import Enum


class Color(str, Enum):
    """
    Enum to use for cli output color. Refer to https://en.wikipedia.org/wiki/ANSI_escape_code#Colors
    for a list of available colors.
    """

    BLACK = "black"
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    BLUE = "blue"
    MAGENTA = "magenta"
    CYAN = "cyan"
    WHITE = "white"


class Level(str, Enum):
    debug = "DEBUG"
    info = "INFO"
    warn = "WARN"
    error = "ERROR"
    off = "OFF"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.__str__()

from enum import Enum


class EchoLevel(str, Enum):
    debug = "DEBUG"
    info = "INFO"
    warn = "WARN"
    error = "ERROR"
    off = "OFF"

    def __str__(self) -> str:
        return self.value

    def __repr__(self) -> str:
        return self.__str__()

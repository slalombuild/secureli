from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

import typer


class Color(str, Enum):
    BLACK = "black"
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    BLUE = "blue"
    MAGENTA = "magenta"
    CYAN = "cyan"
    WHITE = "white"


class EchoAbstraction(ABC):
    """
    Encapsulates the printing purposes, allows us to render stuff to the screen.
    By convention, Echo should only be used by actions, and output based on
    results objects produced by the services (don't sprinkle echo all over the place,
    it harms our ability to refactor!)
    """

    def __init__(self, level: str):
        self.print_enabled = level != "OFF"
        self.info_enabled = level in ["DEBUG", "INFO"]
        self.warn_enabled = level in ["DEBUG", "INFO", "WARN"]
        self.error_enabled = level in ["DEBUG", "INFO", "WARN", "ERROR"]

    @abstractmethod
    def _echo(self, message: str, color: Optional[Color] = None, bold: bool = False):
        """
        Print the provided message to the terminal with the associated color and weight
        :param message: The message to print
        :param color: The color to use
        :param bold: Whether to make this message appear bold or not
        """
        pass

    @abstractmethod
    def confirm(self, message: str, default_response: Optional[bool] = False) -> bool:
        """
        Prompt the user for confirmation
        :param message: The message to display to the user during the prompt
        :param default_response: Whether to default the response to True or False. If
        None, then re-prompt until the user accepts it.
        :return: True if the user confirms, false if not.
        """
        pass

    def print(self, message: str, color: Optional[Color] = None, bold: bool = False):
        """
        Print the provided info message to the terminal with the associated color and weight. Prints
        are never suppressed, unless the level is set to "OFF"
        :param message: The message to print
        :param color: The color to use
        :param bold: Whether to make this message appear bold or not
        """
        if not self.print_enabled:
            return

        self._echo(message, color, bold)

    def info(self, message: str, color: Optional[Color] = None, bold: bool = False):
        """
        Print the provided info message to the terminal with the associated color and weight, unless suppressed
        :param message: The message to print
        :param color: The color to use
        :param bold: Whether to make this message appear bold or not
        """
        if not self.info_enabled:
            return

        self._echo(message, color, bold)

    def error(self, message: str):
        """
        Prints the provided message to the terminal in red and bold
        :param message: The error message to print
        """
        if not self.error_enabled:
            return
        self._echo(message, color=Color.RED, bold=True)

    def warning(self, message: str):
        """
        Prints the provided message to the terminal in red and bold
        :param message: The error message to print
        """
        if not self.warn_enabled:
            return
        self._echo(message, color=Color.YELLOW, bold=False)


class TyperEcho(EchoAbstraction):
    """
    Encapsulates the Typer dependency for printing purposes, allows us to render stuff to the screen.
    """

    def __init__(self, level: str):
        super().__init__(level)

    def _echo(self, message: str, color: Optional[Color] = None, bold: bool = False):
        fg = color.value if color else None
        message = typer.style(message, fg=fg, bold=bold)
        typer.echo(message)

    def confirm(self, message: str, default_response: Optional[bool] = False) -> bool:
        return typer.confirm(message, default=default_response, show_default=True)

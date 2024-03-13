from abc import ABC, abstractmethod
from typing import IO, Optional

import sys
import typer
from secureli.modules.shared.models.echo import Color, Level


class EchoAbstraction(ABC):
    """
    Encapsulates the printing purposes, allows us to render stuff to the screen.
    By convention, Echo should only be used by actions, and output based on
    results objects produced by the services (don't sprinkle echo all over the place,
    it harms our ability to refactor!)
    """

    def __init__(self, level: str):
        self.print_enabled = level != Level.off
        self.debug_enabled = level == Level.debug
        self.info_enabled = level in [Level.debug, Level.info]
        self.warn_enabled = level in [Level.debug, Level.info, Level.warn]
        self.error_enabled = level in [
            Level.debug,
            Level.info,
            Level.warn,
            Level.error,
        ]

    @abstractmethod
    def _echo(
        self,
        message: str,
        color: Optional[Color] = None,
        bold: bool = False,
        fd: IO = sys.stdout,
    ):
        """
        Print the provided message to the terminal with the associated color and weight
        :param message: The message to print
        :param color: The color to use
        :param bold: Whether to make this message appear bold or not
        :param fd: A file descriptor, defaults to stdout
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

    @abstractmethod
    def prompt(self, message: str, default_response: Optional[str] = None) -> str:
        """
        Prompts the user to enter a value
        :param message: The message to display to the user during the prompt
        :param default_response: Whether to default the response to a value. If
        None, then re-prompt until the user accepts it.
        :return: The value that has been entered by the user
        """

    def print(self, message: str, color: Optional[Color] = None, bold: bool = False):
        """
        Print the provided info message to the terminal with the associated color and weight. Prints
        are never suppressed, unless the level is set to "OFF"
        :param message: The message to print
        :param color: The color to use
        :param bold: Whether to make this message appear bold or not
        """
        if self.print_enabled:
            self._echo(message, color, bold)

    def debug(self, message: str) -> None:
        """
        Prints the message to the terminal in blue and bold
        :param message: The debug message to print
        """
        if self.debug_enabled:
            self._echo(f"[DEBUG] {message}", color=Color.BLUE, bold=True)

    def info(self, message: str, color: Optional[Color] = None, bold: bool = False):
        """
        Print the provided info message to the terminal with the associated color and weight, unless suppressed
        :param message: The message to print
        :param color: The color to use
        :param bold: Whether to make this message appear bold or not
        """
        if self.info_enabled:
            self._echo(f"[INFO] {message}", color, bold)

    def error(self, message: str):
        """
        Prints the provided message to the terminal in red and bold
        :param message: The error message to print
        """
        if self.error_enabled:
            self._echo(f"[ERROR] {message}", color=Color.RED, bold=True, fd=sys.stderr)

    def warning(self, message: str):
        """
        Prints the provided message to the terminal in red and bold
        :param message: The error message to print
        """
        if self.warn_enabled:
            self._echo(f"[WARN] {message}", color=Color.YELLOW, bold=False)


class TyperEcho(EchoAbstraction):
    """
    Encapsulates the Typer dependency for printing purposes, allows us to render stuff to the screen.
    """

    def __init__(self, level: str) -> None:
        super().__init__(level)

    def _echo(
        self,
        message: str,
        color: Optional[Color] = None,
        bold: bool = False,
        fd: IO = sys.stdout,
    ) -> None:
        fg = color.value if color else None
        message = typer.style(f"[seCureLI] {message}", fg=fg, bold=bold)
        typer.echo(message, file=fd)

    def confirm(self, message: str, default_response: Optional[bool] = False) -> bool:
        return typer.confirm(message, default=default_response, show_default=True)

    def prompt(self, message: str, default_response: Optional[str] = None) -> str:
        return typer.prompt(
            text=message,
            default=default_response,
            show_default=True if default_response else False,
        )

from secureli.abstractions.echo import EchoAbstraction, Color
from secureli.services.logging import LoggingService, LogAction


class YetiAction:
    """
    An action responsible for displaying the Securyeti ASCII art in the terminal during the `yeti` command.
    """

    def __init__(self, yeti_data: str, echo: EchoAbstraction, logging: LoggingService):
        self.yeti_data = yeti_data
        self.echo = echo
        self.logging = logging

    def print_yeti(self, color: Color):
        """
        Use the provided color and echo service to print the Securyeti to the terminal
        :param color:
        :return:
        """
        self.echo.print(self.yeti_data, color=color, bold=True)

        self.logging.success(LogAction.yeti)

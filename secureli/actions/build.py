from secureli.abstractions.echo import EchoAbstraction, Color
from secureli.services.logging import LoggingService, LogAction


class BuildAction:
    """
    An action responsible for displaying the Securbuild ASCII art in the terminal during the `build` command.
    """

    def __init__(self, build_data: str, echo: EchoAbstraction, logging: LoggingService):
        self.build_data = build_data
        self.echo = echo
        self.logging = logging

    def print_build(self, color: Color):
        """
        Use the provided color and echo service to print the Securbuild to the terminal
        :param color:
        :return:
        """
        self.echo.print(self.build_data, color=color, bold=True)

        self.logging.success(LogAction.build)

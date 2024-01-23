from unittest.mock import MagicMock

import pytest

from secureli.actions.build import BuildAction
from secureli.models.echo import Color


@pytest.fixture()
def mock_build_data() -> str:
    return "MOCK BUILD"


@pytest.fixture()
def build_action(mock_build_data, mock_echo, mock_logging_service) -> BuildAction:
    return BuildAction(
        build_data=mock_build_data, echo=mock_echo, logging=mock_logging_service
    )


def test_that_build_action_respects_color_choice(
    build_action: BuildAction,
    mock_echo: MagicMock,
    mock_build_data: str,
):
    build_action.print_build(color=Color.MAGENTA)

    mock_echo.print.assert_called_once_with(
        mock_build_data, color=Color.MAGENTA, bold=True
    )

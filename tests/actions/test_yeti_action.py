from unittest.mock import MagicMock

import pytest

from secureli.actions.yeti import YetiAction
from secureli.abstractions.echo import Color


@pytest.fixture()
def mock_yeti_data() -> str:
    return "MOCK YETI"


@pytest.fixture()
def yeti_action(mock_yeti_data, mock_echo, mock_logging_service) -> YetiAction:
    return YetiAction(
        yeti_data=mock_yeti_data, echo=mock_echo, logging=mock_logging_service
    )


def test_that_yeti_action_respects_color_choice(
    yeti_action: YetiAction,
    mock_echo: MagicMock,
    mock_yeti_data: str,
):
    yeti_action.print_yeti(color=Color.MAGENTA)

    mock_echo.print.assert_called_once_with(
        mock_yeti_data, color=Color.MAGENTA, bold=True
    )

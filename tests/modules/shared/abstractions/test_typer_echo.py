from pytest_mock import MockerFixture
from secureli.modules.shared.abstractions.echo import TyperEcho
from unittest.mock import MagicMock, ANY

import pytest
from secureli.modules.shared.models.echo import Color, Level

ECHO_SECURELI_PREFIX = "[seCureLI]"


@pytest.fixture()
def mock_echo_text() -> str:
    return "Hello, There"


@pytest.fixture()
def mock_typer_style(mock_echo_text: str, mocker: MockerFixture) -> MagicMock:
    mock_typer_style = mocker.patch("typer.style")
    mock_typer_style.return_value = mock_echo_text
    return mock_typer_style


@pytest.fixture()
def mock_typer_confirm(mocker: MockerFixture) -> MagicMock:
    mock_typer_style = mocker.patch("typer.confirm")
    mock_typer_style.return_value = True
    return mock_typer_style


@pytest.fixture()
def mock_typer_prompt(mocker: MockerFixture) -> MagicMock:
    mock_typer_style = mocker.patch("typer.prompt")
    mock_typer_style.return_value = "prompt value"
    return mock_typer_style


@pytest.fixture()
def mock_typer_echo(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("typer.echo")


@pytest.fixture()
def typer_echo(request) -> TyperEcho:
    return TyperEcho(level=request.param)


@pytest.mark.parametrize(
    "typer_echo",
    [Level.info, Level.debug, Level.error, Level.warn],
    indirect=True,
)
def test_that_typer_echo_renders_print_messages_correctly(
    typer_echo: TyperEcho,
    mock_echo_text: str,
    mock_typer_style: MagicMock,
    mock_typer_echo: MagicMock,
):
    typer_echo.print(mock_echo_text, Color.BLACK, bold=True)

    mock_typer_style.assert_called_once_with(
        f"{ECHO_SECURELI_PREFIX} {mock_echo_text}", fg=Color.BLACK.value, bold=True
    )
    mock_typer_echo.assert_called_once_with(mock_echo_text, file=ANY)


@pytest.mark.parametrize(
    "typer_echo",
    [
        Level.debug,
        Level.info,
        Level.warn,
        Level.error,
    ],
    indirect=True,
)
def test_that_typer_echo_renders_errors_correctly(
    typer_echo: TyperEcho,
    mock_echo_text: str,
    mock_typer_style: MagicMock,
):
    typer_echo.error(mock_echo_text)

    mock_typer_style.assert_called_once_with(
        f"{ECHO_SECURELI_PREFIX} [ERROR] {mock_echo_text}",
        fg=Color.RED.value,
        bold=True,
    )


@pytest.mark.parametrize(
    "typer_echo", [Level.warn, Level.info, Level.debug], indirect=True
)
def test_that_typer_echo_renders_warnings_correctly(
    typer_echo: TyperEcho,
    mock_echo_text: str,
    mock_typer_style: MagicMock,
):
    typer_echo.warning(mock_echo_text)

    mock_typer_style.assert_called_once_with(
        f"{ECHO_SECURELI_PREFIX} [WARN] {mock_echo_text}",
        fg=Color.YELLOW.value,
        bold=False,
    )


@pytest.mark.parametrize("typer_echo", [Level.info, Level.debug], indirect=True)
def test_that_typer_echo_renders_info_correctly(
    typer_echo: TyperEcho,
    mock_echo_text: str,
    mock_typer_style: MagicMock,
):
    typer_echo.info(mock_echo_text, color=Color.MAGENTA, bold=True)

    mock_typer_style.assert_called_once_with(
        f"{ECHO_SECURELI_PREFIX} [INFO] {mock_echo_text}",
        fg=Color.MAGENTA.value,
        bold=True,
    )


@pytest.mark.parametrize(
    "typer_echo",
    [Level.debug],
    indirect=True,
)
def test_that_typer_echo_renders_debug_messages_correctly(
    typer_echo: TyperEcho,
    mock_echo_text: str,
    mock_typer_style: MagicMock,
):
    typer_echo.debug(mock_echo_text)
    mock_typer_style.assert_called_once_with(
        f"{ECHO_SECURELI_PREFIX} [DEBUG] {mock_echo_text}", fg=Color.BLUE, bold=True
    )


@pytest.mark.parametrize(
    "typer_echo",
    [Level.off],
    indirect=True,
)
def test_that_typer_echo_suppresses_all_messages_when_off(
    mock_echo_text: str,
    mock_typer_style: MagicMock,
    typer_echo: TyperEcho,
):
    typer_echo.info(mock_echo_text)
    typer_echo.warning(mock_echo_text)
    typer_echo.error(mock_echo_text)
    typer_echo.debug(mock_echo_text)
    typer_echo.print(mock_echo_text)

    mock_typer_style.assert_not_called()


@pytest.mark.parametrize(
    "typer_echo",
    [Level.off],
    indirect=True,
)
def test_that_typer_echo_suppresses_error_messages(
    mock_echo_text: str, mock_typer_style: MagicMock, typer_echo: TyperEcho
):
    typer_echo.error(mock_echo_text)
    mock_typer_style.assert_not_called()


@pytest.mark.parametrize(
    "typer_echo",
    [Level.error, Level.off],
    indirect=True,
)
def test_that_typer_echo_suppresses_warning_messages(
    mock_echo_text: str, mock_typer_style: MagicMock, typer_echo: TyperEcho
):
    typer_echo.warning(mock_echo_text)
    mock_typer_style.assert_not_called()


@pytest.mark.parametrize(
    "typer_echo",
    [Level.warn, Level.error, Level.off],
    indirect=True,
)
def test_that_typer_echo_suppresses_info_messages(
    mock_echo_text: str, mock_typer_style: MagicMock, typer_echo: TyperEcho
):
    typer_echo.info(mock_echo_text)
    mock_typer_style.assert_not_called()


@pytest.mark.parametrize(
    "typer_echo",
    [Level.info, Level.warn, Level.error, Level.off],
    indirect=True,
)
def test_that_typer_echo_suppresses_debug_messages(
    mock_echo_text: str, mock_typer_style: MagicMock, typer_echo: TyperEcho
):
    typer_echo.debug(mock_echo_text)
    mock_typer_style.assert_not_called()


@pytest.mark.parametrize(
    "typer_echo",
    [Level.info],
    indirect=True,
)
def test_that_typer_echo_prompts_user_for_confirmation(
    typer_echo: TyperEcho,
    mock_echo_text: str,
    mock_typer_confirm: MagicMock,
):
    typer_echo.confirm(mock_echo_text)

    mock_typer_confirm.assert_called_once()


def test_that_typer_echo_implements_prompt_with_default(mock_typer_prompt: MagicMock):
    typer_echo = TyperEcho(level=Level.info)
    message = "test message"
    default_response = "default user response"
    typer_echo.prompt(message=message, default_response=default_response)

    mock_typer_prompt.assert_called_once_with(
        text=message, default=default_response, show_default=True
    )


def test_that_typer_echo_implements_prompt_without_default(
    mock_typer_prompt: MagicMock,
):
    typer_echo = TyperEcho(level=Level.info)
    message = "test message"
    typer_echo.prompt(message=message)

    mock_typer_prompt.assert_called_once_with(
        text=message, default=None, show_default=False
    )

from unittest.mock import MagicMock, ANY

import pytest
from pytest_mock import MockerFixture

from secureli.abstractions.echo import TyperEcho, Color


@pytest.fixture()
def mock_echo_text() -> str:
    return "Hello, There"


@pytest.fixture()
def mock_typer_style(mock_echo_text: str, mocker: MockerFixture) -> MagicMock:
    mock_typer_style = mocker.patch("typer.style")
    mock_typer_style.return_value = mock_echo_text
    return mock_typer_style


@pytest.fixture()
def mock_typer_confirm(mock_echo_text: str, mocker: MockerFixture) -> MagicMock:
    mock_typer_style = mocker.patch("typer.confirm")
    mock_typer_style.return_value = True
    return mock_typer_style


@pytest.fixture()
def mock_typer_echo(mocker: MockerFixture) -> MagicMock:
    return mocker.patch("typer.echo")


@pytest.fixture()
def typer_echo(
    mock_typer_style: MagicMock,
    mock_typer_echo: MagicMock,
) -> TyperEcho:
    return TyperEcho(level="DEBUG")


@pytest.fixture()
def typer_echo_logging_off(
    mock_typer_style: MagicMock,
    mock_typer_echo: MagicMock,
) -> TyperEcho:
    return TyperEcho(level="OFF")


def test_that_typer_echo_stylizes_message(
    typer_echo: TyperEcho,
    mock_echo_text: str,
    mock_typer_style: MagicMock,
    mock_typer_echo: MagicMock,
):
    typer_echo.info(mock_echo_text)

    mock_typer_style.assert_called_once()
    mock_typer_echo.assert_called_once_with(mock_echo_text)


def test_that_typer_echo_stylizes_message_when_printing(
    typer_echo: TyperEcho,
    mock_echo_text: str,
    mock_typer_style: MagicMock,
    mock_typer_echo: MagicMock,
):
    typer_echo.print(mock_echo_text)

    mock_typer_style.assert_called_once()
    mock_typer_echo.assert_called_once_with(mock_echo_text)


def test_that_typer_echo_does_not_even_print_when_off(
    typer_echo_logging_off: TyperEcho,
    mock_echo_text: str,
    mock_typer_style: MagicMock,
    mock_typer_echo: MagicMock,
):
    typer_echo_logging_off.print(mock_echo_text)

    mock_typer_style.assert_not_called()


def test_that_typer_echo_errors_are_red(
    typer_echo: TyperEcho,
    mock_echo_text: str,
    mock_typer_style: MagicMock,
    mock_typer_echo: MagicMock,
):
    typer_echo.error(mock_echo_text)

    mock_typer_style.assert_called_once_with(ANY, fg="red", bold=ANY)


def test_that_typer_echo_warnings_are_yellow(
    typer_echo: TyperEcho,
    mock_echo_text: str,
    mock_typer_style: MagicMock,
    mock_typer_echo: MagicMock,
):
    typer_echo.warning(mock_echo_text)

    mock_typer_style.assert_called_once_with(ANY, fg="yellow", bold=ANY)


def test_that_typer_echo_info_match_color_choice(
    typer_echo: TyperEcho,
    mock_echo_text: str,
    mock_typer_style: MagicMock,
    mock_typer_echo: MagicMock,
):
    typer_echo.info(mock_echo_text, color=Color.MAGENTA, bold=True)

    mock_typer_style.assert_called_once_with(ANY, fg="magenta", bold=True)


def test_that_typer_echo_suppresses_messages_when_off(
    typer_echo_logging_off: TyperEcho,
    mock_echo_text: str,
    mock_typer_style: MagicMock,
    mock_typer_echo: MagicMock,
):
    typer_echo_logging_off.info(mock_echo_text)
    typer_echo_logging_off.warning(mock_echo_text)
    typer_echo_logging_off.error(mock_echo_text)

    mock_typer_style.assert_not_called()


def test_that_typer_echo_prompts_user_for_confirmation(
    typer_echo: TyperEcho,
    mock_echo_text: str,
    mock_typer_confirm: MagicMock,
):
    typer_echo.confirm(mock_echo_text)

    mock_typer_confirm.assert_called_once()

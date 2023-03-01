from pathlib import Path
from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from secureli.abstractions.lexer_guesser import PygmentsLexerGuesser


@pytest.fixture()
def good_file_path() -> Path:
    return Path("path/to/file.txt")


@pytest.fixture()
def pygments_lexer_guesser(mocker: MockerFixture) -> PygmentsLexerGuesser:
    mock_pygments = mocker.patch("pygments.lexers")
    mock_lexer = MagicMock()
    mock_lexer.name = "RadLang"
    mock_pygments.guess_lexer_for_filename.return_value = mock_lexer
    return PygmentsLexerGuesser()


def test_that_pygments_lexer_guesser_guesses_lexer_with_pygments(
    pygments_lexer_guesser: PygmentsLexerGuesser,
    good_file_path: Path,
):
    lexer = pygments_lexer_guesser.guess_lexer(good_file_path, "file_contents")

    assert lexer == "RadLang"

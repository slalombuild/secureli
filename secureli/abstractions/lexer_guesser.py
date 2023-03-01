from abc import ABC, abstractmethod
from pathlib import Path

import pygments.lexers


class LexerGuesser(ABC):
    """Represents guessing the lexer for a given file."""

    @abstractmethod
    def guess_lexer(self, file_path: Path, file_contents: str) -> str:
        pass


class PygmentsLexerGuesser(LexerGuesser):
    """Pygments-implementation of LexerGuesser"""

    def guess_lexer(self, file_path: Path, file_contents: str) -> str:
        lexer = pygments.lexers.guess_lexer_for_filename(file_path, file_contents)
        return lexer.name

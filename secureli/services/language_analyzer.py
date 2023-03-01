from collections import defaultdict
from pathlib import Path

import pydantic

from secureli.abstractions.lexer_guesser import LexerGuesser
from secureli.repositories.repo_files import RepoFilesRepository
from secureli.services.language_support import supported_languages


class SkippedFile(pydantic.BaseModel):
    """
    A file skipped by the analysis phase.
    """

    file_path: Path
    error_message: str


class AnalyzeResult(pydantic.BaseModel):
    """
    The result of the analysis phase.
    """

    language_proportions: dict[str, float]
    skipped_files: list[SkippedFile]


class LanguageAnalyzerService:
    """
    Analyzes a repository's visible files to determine which language SeCureLI is targeting.
    """

    def __init__(
        self,
        repo_files: RepoFilesRepository,
        lexer_guesser: LexerGuesser,
    ):
        self.repo_files = repo_files
        self.lexer_guesser = lexer_guesser

    def analyze(self, folder_path: Path) -> AnalyzeResult:
        """
        Analyzes the folder structure and lists languages found
        :param folder_path: The path to the repository to analyze
        :return: Produces an ordered dictionary of languages detected and what percentage
        of the repo is each language. For example, if 60% of the repo is Python files and
        40% of the repo is JavaScript, the result will be a dictionary containing keys
        "Python" and "JavaScript" with values 0.6 and 0.4 respectively
        """
        file_paths = self.repo_files.list_repo_files(folder_path)
        results = defaultdict(int)

        skipped_files = []
        for file_path in file_paths:
            try:
                text = self.repo_files.load_file(file_path)
                lexer = self.lexer_guesser.guess_lexer(file_path, text)
                results[lexer] += 1
            except ValueError as value_error:
                skipped_files.append(
                    SkippedFile(file_path=file_path, error_message=str(value_error))
                )

        return AnalyzeResult(
            language_proportions=self._process_counts_to_ratios_per_language(results),
            skipped_files=skipped_files,
        )

    def _process_counts_to_ratios_per_language(
        self, results: dict[str, int]
    ) -> dict[str, float]:
        """
        Removes unsupported languages and calculates a ratio of how frequently the
        language appeared in repo files for each supported language
        :param results: A dictionary of all languages and counts for how many files
        were evaluated to that language (i.e. Python, 5 files; JavaScript 3 files)
        :return: A dictionary of all supported languages and a scale of 0-1 of how
        much of the repo is that language (i.e. Python, 0.625; JavaScript, 0.375)
        """
        # Sort the keys by how many files matched each lexer
        sorted_keys = sorted(results.keys(), key=lambda x: results[x], reverse=True)

        # Filter out the keys that aren't in the list of supported languages
        filtered_keys = {
            key: results[key] for key in sorted_keys if key in supported_languages
        }

        # Count the number of files in the remaining dictionary of supported lexers
        total_filtered_files = sum(filtered_keys.values())

        # Calculate a new value based on the number of matching files over the total files
        return {
            key: value / total_filtered_files for key, value in filtered_keys.items()
        }

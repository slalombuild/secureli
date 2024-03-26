import pathspec

from secureli.settings import Settings


class SecureliIgnoreService:
    """
    Looks for and translates the .secureli.yaml file's pre-commit global exclusion
    paths into a set of regular expressions that match all files found
    """

    def __init__(self, settings: Settings):
        self.settings = settings

    def ignored_file_patterns(self) -> list[str]:
        """
        Calculate the regular expressions to ignore from .secureli.yaml file's pre-commit
        global exclusion paths, assuming it follows the same structure as a .gitignore file
        :return: A list of regular expression pattern strings, or empty array if the
        file is empty or missing.
        """
        if not self.settings.repo_files.exclude_file_patterns:
            return []

        pathspec_lines = pathspec.PathSpec.from_lines(
            pathspec.patterns.GitWildMatchPattern,
            self.settings.repo_files.exclude_file_patterns,
        )
        raw_patterns = [
            pathspec_pattern.regex.pattern
            for pathspec_pattern in pathspec_lines.patterns
            if pathspec_pattern.include
        ]

        return raw_patterns

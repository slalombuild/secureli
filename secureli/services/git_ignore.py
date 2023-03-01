from pathlib import Path

import pathspec


class BadIgnoreBlockError(Exception):
    pass


class GitIgnoreService:
    """
    Manages entries in a consuming repository's gitignore so that secureli doesn't
    become convinced that local setup was done that was actually done on a different
    environment.
    """

    header = "# Secureli-generated files (do not modify):"
    ignore_entries = [".secureli"]
    footer = "# End Secureli-generated files"
    git_ignore_path = Path("./.gitignore")

    def ignore_secureli_files(self):
        """Creates a .gitignore, appends to an existing one, or updates the configuration"""
        if not self.git_ignore_path.exists():
            # your repo doesn't have a gitignore? That's a bold move.
            self._create_git_ignore()
        else:
            self._update_git_ignore()

    def ignored_file_patterns(self) -> list[str]:
        if not self.git_ignore_path.exists():
            return []

        """Reads the lines from the .gitignore file"""
        file_contents = self._read_file_contents()
        lines = file_contents.splitlines(keepends=False)
        pathspec_lines = pathspec.PathSpec.from_lines(
            pathspec.patterns.GitWildMatchPattern, lines
        )
        raw_patterns = [
            pathspec_pattern.regex.pattern
            for pathspec_pattern in pathspec_lines.patterns
            if pathspec_pattern.include
        ]
        return raw_patterns

    def _generate_git_ignore_block(self) -> str:
        """
        Create a .gitignore block of our ignore entries wrapped by a constant header and footer
        :return: The rendered block, with wrapping new-lines
        """
        combined_entries = str.join("\n", self.ignore_entries)
        return f"\n{self.header}\n{combined_entries}\n{self.footer}\n"

    def _create_git_ignore(self):
        """Creates a .gitignore file for a repo that doesn't have one at all"""
        self._write_file_contents(self._generate_git_ignore_block())

    def _update_git_ignore(self):
        """
        Updates the .gitignore to add our block at the end if it's missing,
        or update it in place if it's present already
        """
        contents = self._read_file_contents()
        header_start_location = contents.find(self.header)

        if header_start_location == -1:
            # append our block to the end of the existing contents
            contents += self._generate_git_ignore_block()
            self._write_file_contents(contents)

        else:
            footer_start_location = contents.find(self.footer)
            if footer_start_location == -1:
                raise BadIgnoreBlockError(
                    "Could not find the end of the secureli-managed block of .gitignore, "
                    "but found the start. Has someone adjusted this file? Please remove "
                    "the entire secureli-block and try to run this again."
                )

            before_contents = contents[: header_start_location - 1]
            after_contents = contents[footer_start_location + len(self.footer) + 1 :]
            new_contents = (
                f"{before_contents}{self._generate_git_ignore_block()}{after_contents}"
            )
            self._write_file_contents(new_contents)

    def _write_file_contents(self, contents: str):
        """Update the .gitignore file with the provided contents"""
        with open(self.git_ignore_path, "w") as f:
            f.write(contents)

    def _read_file_contents(self) -> str:
        """Read the .gitignore file"""
        with open(self.git_ignore_path, "r") as f:
            return f.read()

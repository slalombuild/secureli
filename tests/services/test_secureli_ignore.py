import pytest

from secureli.services.secureli_ignore import SecureliIgnoreService
from secureli.settings import (
    Settings,
    RepoFilesSettings,
    PreCommitSettings,
    LanguageSupportSettings,
    EchoSettings,
)


@pytest.fixture()
def repo_files() -> RepoFilesSettings:
    return RepoFilesSettings()


@pytest.fixture()
def echo() -> EchoSettings:
    return EchoSettings()


@pytest.fixture()
def language_support() -> LanguageSupportSettings:
    return LanguageSupportSettings()


@pytest.fixture()
def pre_commit() -> PreCommitSettings:
    return PreCommitSettings()


@pytest.fixture()
def settings(
    repo_files: RepoFilesSettings,
    echo: EchoSettings,
    language_support: LanguageSupportSettings,
    pre_commit: PreCommitSettings,
) -> Settings:
    return Settings(
        repo_files=repo_files,
        echo=echo,
        language_support=language_support,
        pre_commit=pre_commit,
    )


@pytest.fixture
def secureli_ignore(settings: Settings) -> SecureliIgnoreService:
    return SecureliIgnoreService(settings)


def test_that_secureli_ignore_handles_empty_ignored_file_patterns(
    secureli_ignore: SecureliIgnoreService,
):
    ignored_patterns = secureli_ignore.ignored_file_patterns()

    assert not ignored_patterns


def test_that_secureli_ignore_finds_and_reads_file(
    secureli_ignore: SecureliIgnoreService,
    settings: Settings,
):
    settings.repo_files.exclude_file_patterns = ["*.py", "*.txt"]
    ignored_patterns = secureli_ignore.ignored_file_patterns()

    assert ignored_patterns == [
        "^(?:.+/)?[^/]*\\.py(?:(?P<ps_d>/).*)?$",
        "^(?:.+/)?[^/]*\\.txt(?:(?P<ps_d>/).*)?$",
    ]

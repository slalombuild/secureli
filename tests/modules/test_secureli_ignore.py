import pytest

from secureli.modules.secureli_ignore import SecureliIgnoreService
from secureli.repositories import repo_settings
from secureli.settings import Settings


@pytest.fixture()
def repo_files() -> repo_settings.RepoFilesSettings:
    return repo_settings.RepoFilesSettings()


@pytest.fixture()
def echo() -> repo_settings.EchoSettings:
    return repo_settings.EchoSettings()


@pytest.fixture()
def language_support() -> repo_settings.LanguageSupportSettings:
    return repo_settings.LanguageSupportSettings()


@pytest.fixture()
def settings(
    repo_files: repo_settings.RepoFilesSettings,
    echo: repo_settings.EchoSettings,
    language_support: repo_settings.LanguageSupportSettings,
) -> Settings:
    return Settings(
        repo_files=repo_files,
        echo=echo,
        language_support=language_support,
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

import pytest

from secureli.modules.secureli_ignore import SecureliIgnoreService
from secureli import settings


@pytest.fixture()
def repo_files() -> settings.RepoFilesSettings:
    return settings.RepoFilesSettings()


@pytest.fixture()
def echo() -> settings.EchoSettings:
    return settings.EchoSettings()


@pytest.fixture()
def language_support() -> settings.LanguageSupportSettings:
    return settings.LanguageSupportSettings()


@pytest.fixture()
def settings_fixture(
    repo_files: settings.RepoFilesSettings,
    echo: settings.EchoSettings,
    language_support: settings.LanguageSupportSettings,
) -> settings.Settings:
    return settings.Settings(
        repo_files=repo_files,
        echo=echo,
        language_support=language_support,
    )


@pytest.fixture
def secureli_ignore_fixture(
    settings_fixture: settings.Settings,
) -> SecureliIgnoreService:
    return SecureliIgnoreService(settings_fixture)


def test_that_secureli_ignore_handles_empty_ignored_file_patterns(
    secureli_ignore_fixture: SecureliIgnoreService,
):
    ignored_patterns = secureli_ignore_fixture.ignored_file_patterns()

    assert not ignored_patterns


def test_that_secureli_ignore_finds_and_reads_file(
    secureli_ignore_fixture: SecureliIgnoreService,
    settings_fixture: settings.Settings,
):
    settings_fixture.repo_files.exclude_file_patterns = ["*.py", "*.txt"]
    ignored_patterns = secureli_ignore_fixture.ignored_file_patterns()

    assert ignored_patterns == [
        "^(?:.+/)?[^/]*\\.py(?:(?P<ps_d>/).*)?$",
        "^(?:.+/)?[^/]*\\.txt(?:(?P<ps_d>/).*)?$",
    ]

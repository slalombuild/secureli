from unittest.mock import MagicMock

import pytest
from _pytest.python_api import raises
from pytest_mock import MockerFixture

from secureli.abstractions.pre_commit import (
    InstallResult,
)
from secureli.services.language_support import (
    LanguageSupportService,
    LinterConfig,
    LinterConfigData,
    LinterConfigWriteResult,
)
from secureli.services.language_config import (
    LanguageConfigService,
    LanguagePreCommitResult,
    LoadLinterConfigsResult,
)


@pytest.fixture()
def mock_open_config(mocker: MockerFixture):
    mock_open = mocker.mock_open(
        read_data="""
    exclude: some-exclude-regex
    repos:
    - hooks:
      - id: some-test-hook
      repo: xyz://some-test-repo-url
      rev: 1.0.0
    - hooks:
      - id: some-other-test-hook
      repo: xyz://some-other-test-repo-url
      rev: 1.0.0
    """
    )
    mocker.patch("builtins.open", mock_open)
    mock_open.return_value.write = MagicMock()
    return mock_open


@pytest.fixture()
def mock_hashlib(mocker: MockerFixture) -> MagicMock:
    mock_hashlib = MagicMock()
    mock_md5 = MagicMock()
    mock_hashlib.md5.return_value = mock_md5
    mock_md5.hexdigest.return_value = "mock-hash-code"
    mocker.patch("secureli.utilities.hash.hashlib", mock_hashlib)
    return mock_hashlib


@pytest.fixture()
def mock_hashlib_no_match(mocker: MockerFixture) -> MagicMock:
    mock_hashlib = MagicMock()
    mock_md5 = MagicMock()
    mock_hashlib.md5.return_value = mock_md5
    mock_md5.hexdigest.side_effect = ["first-hash-code", "second-hash-code"]
    mocker.patch("secureli.utilities.hash.hashlib", mock_hashlib)
    return mock_hashlib


@pytest.fixture()
def mock_pre_commit_hook() -> MagicMock:
    mock_pre_commit_hook = MagicMock()
    mock_pre_commit_hook.install.return_value = InstallResult(
        successful=True,
    )

    return mock_pre_commit_hook


@pytest.fixture()
def mock_data_loader() -> MagicMock:
    mock_data_loader = MagicMock()
    mock_data_loader.return_value = "a: 1"
    return mock_data_loader


@pytest.fixture()
def mock_git_ignore() -> MagicMock:
    mock_git_ignore = MagicMock()
    return mock_git_ignore


@pytest.fixture()
def mock_echo() -> MagicMock:
    mock_echo = MagicMock()
    return mock_echo


@pytest.fixture()
def mock_language_config_service() -> LanguageConfigService:
    mock_language_config_service = MagicMock()

    return mock_language_config_service


@pytest.fixture()
def language_support_service(
    mock_pre_commit_hook: MagicMock,
    mock_git_ignore: MagicMock,
    mock_language_config_service: MagicMock,
    mock_data_loader: MagicMock,
) -> LanguageSupportService:
    return LanguageSupportService(
        pre_commit_hook=mock_pre_commit_hook,
        git_ignore=mock_git_ignore,
        language_config=mock_language_config_service,
        data_loader=mock_data_loader,
    )


def test_that_language_support_identifies_a_security_hook_we_can_use_during_init(
    language_support_service: LanguageSupportService,
    mock_data_loader: MagicMock,
    mock_language_config_service: MagicMock,
):
    def mock_loader_side_effect(resource):
        return """
            http://sample-repo.com/baddie-finder:
                - baddie-finder-hook
        """

    mock_language_config_service.get_language_config.return_value = LanguagePreCommitResult(
        language="Python",
        version="abc123",
        linter_config=LoadLinterConfigsResult(successful=False, linter_data=list()),
        config_data="""
            repos:
            -   repo: http://sample-repo.com/baddie-finder
                hooks:
                -    id: baddie-finder-hook
            """,
    )

    mock_data_loader.side_effect = mock_loader_side_effect

    hook_id = language_support_service.secret_detection_hook_id(["Python"])

    assert hook_id == "baddie-finder-hook"


def test_that_language_support_does_not_identify_a_security_hook_if_config_does_not_use_repo_even_if_hook_id_matches(
    language_support_service: LanguageSupportService,
    mock_data_loader: MagicMock,
    mock_language_config_service: MagicMock,
):
    def mock_loader_side_effect(resource):
        return """
            http://sample-repo.com/baddie-finder:
                - baddie-finder-hook
        """

    mock_language_config_service.get_language_config.return_value = LanguagePreCommitResult(
        language="Python",
        version="abc123",
        linter_config=LoadLinterConfigsResult(successful=False, linter_data=list()),
        config_data="""
            repos:
            -   repo: http://sample-repo.com/goodie-finder # does not match our secrets_detectors
                hooks:
                -    id: baddie-finder-hook
            """,
    )

    mock_data_loader.side_effect = mock_loader_side_effect

    hook_id = language_support_service.secret_detection_hook_id(["Python"])

    assert hook_id is None


def test_that_language_support_calculates_a_serializable_hook_configuration(
    language_support_service: LanguageSupportService,
    mock_language_config_service: LanguageConfigService,
):
    mock_language_config_service.get_language_config.return_value = LanguagePreCommitResult(
        language="Python",
        version="abc123",
        linter_config=LoadLinterConfigsResult(successful=False, linter_data=list()),
        config_data="""
        repos:
        -   repo: http://sample-repo.com/hooks
            rev: 1.0.25
            hooks:
            -    id: hook-a
            -    id: hook-b
        """,
    )

    hook_configuration = language_support_service.get_configuration(["RadLang"])
    assert len(hook_configuration.repos) == 2
    assert hook_configuration.repos[0].revision == "1.0.25"
    assert len(hook_configuration.repos[0].hooks) == 2
    assert "hook-a" in hook_configuration.repos[0].hooks


def test_that_language_support_does_not_identify_a_security_hook_if_config_uses_matching_repo_but_not_matching_hook(
    language_support_service: LanguageSupportService,
    mock_data_loader: MagicMock,
    mock_language_config_service: MagicMock,
):
    def mock_loader_side_effect(resource):
        return """
            http://sample-repo.com/baddie-finder:
                - baddie-finder-hook
        """

    mock_language_config_service.get_language_config.return_value = LanguagePreCommitResult(
        language="Python",
        version="abc123",
        linter_config=LoadLinterConfigsResult(successful=False, linter_data=list()),
        config_data="""
            repos:
            -   repo: http://sample-repo.com/baddie-finder
                hooks:
                -    id: goodie-finder-hook # does not match our secrets_detectors
            """,
    )

    mock_data_loader.side_effect = mock_loader_side_effect

    hook_id = language_support_service.secret_detection_hook_id(["Python"])

    assert hook_id is None


# #### _write_pre_commit_configs ####
def test_that_language_support_writes_linter_config_files(
    language_support_service: LanguageSupportService,
    mock_language_config_service: MagicMock,
    mock_data_loader: MagicMock,
    mock_open: MagicMock,
    mock_pre_commit_hook: MagicMock,
):
    def mock_loader_side_effect(resource):
        return """
            http://sample-repo.com/baddie-finder:
                - baddie-finder
        """

    mock_language_config_service.get_language_config.return_value = LanguagePreCommitResult(
        language="Python",
        version="abc123",
        linter_config=LoadLinterConfigsResult(
            successful=True,
            linter_data=[{"filename": "test.txt", "settings": {}}],
        ),
        config_data="""
            repos:
            -   repo: http://sample-repo.com/baddie-finder
                hooks:
                -    id: baddie-finder
            """,
    )

    mock_data_loader.side_effect = mock_loader_side_effect

    languages = ["RadLang"]
    lint_languages = [*languages]

    build_config_result = language_support_service.build_pre_commit_config(
        languages, lint_languages
    )

    metadata = language_support_service.apply_support(
        ["RadLang"], build_config_result, overwrite_pre_commit=True
    )

    assert metadata.security_hook_id == "baddie-finder"


def test_that_language_support_throws_exception_when_language_config_file_cannot_be_opened(
    language_support_service: LanguageSupportService,
    mock_language_config_service: MagicMock,
    mock_open: MagicMock,
):
    mock_language_config_service.get_language_config.return_value = LanguagePreCommitResult(
        language="Python",
        version="abc123",
        linter_config=LoadLinterConfigsResult(
            successful=True,
            linter_data=[{"filename": "test.txt", "settings": {}}],
        ),
        config_data="""
                repos:
                -   repo: http://sample-repo.com/baddie-finder
                    hooks:
                    -    id: baddie-finder
                """,
    )

    languages = ["RadLang"]
    lint_languages = [*languages]

    build_config_result = language_support_service.build_pre_commit_config(
        languages, lint_languages
    )

    mock_open.side_effect = IOError

    with raises(IOError):
        language_support_service.apply_support(
            languages, build_config_result, overwrite_pre_commit=True
        )


def test_that_language_support_handles_invalid_language_config(
    language_support_service: LanguageSupportService,
    mock_language_config_service: MagicMock,
    mock_open: MagicMock,
):
    mock_language_config_service.get_language_config.return_value = (
        LanguagePreCommitResult(
            language="Python",
            version="abc123",
            linter_config=LoadLinterConfigsResult(
                successful=True,
                linter_data=[{"filename": "test.txt", "settings": {}}],
            ),
            config_data="",
        )
    )

    languages = ["RadLang"]
    lint_languages = [*languages]

    build_config_result = language_support_service.build_pre_commit_config(
        languages, lint_languages
    )

    metadata = language_support_service.apply_support(
        languages, build_config_result, overwrite_pre_commit=True
    )
    assert metadata.security_hook_id is None


def test_that_language_support_handles_empty_repos_list(
    language_support_service: LanguageSupportService,
    mock_language_config_service: MagicMock,
    mock_data_loader: MagicMock,
):
    mock_language_config_service.get_language_config.return_value = LanguagePreCommitResult(
        language="Python",
        version="abc123",
        linter_config=LoadLinterConfigsResult(
            successful=True,
            linter_data=[{"filename": "test.txt", "settings": {}}],
        ),
        config_data="""
            repos:
            """,
    )

    mock_data_loader.return_value = ""

    languages = ["RadLang"]
    lint_languages = [*languages]

    build_config_result = language_support_service.build_pre_commit_config(
        languages, lint_languages
    )

    assert build_config_result.config_data["repos"] == []


def test_write_pre_commit_configs_writes_successfully(
    language_support_service: LanguageSupportService,
    mock_open: MagicMock,
):
    configs = [
        LinterConfig(
            language="RadLag",
            linter_data=[
                LinterConfigData(
                    filename="rad-lint.yml",
                    settings={},
                )
            ],
        ),
        LinterConfig(
            language="CoolLang",
            linter_data=[
                LinterConfigData(
                    filename="cool-lint.yml",
                    settings={},
                )
            ],
        ),
    ]
    language_support_service._write_pre_commit_configs(configs)

    assert mock_open.call_count == len(configs)
    assert mock_open.return_value.write.call_count == len(configs)


def test_write_pre_commit_configs_ignores_empty_linter_arr(
    language_support_service: LanguageSupportService,
    mock_open: MagicMock,
):
    language_support_service._write_pre_commit_configs([])

    mock_open.assert_not_called()
    mock_open.return_value.write.assert_not_called()


def test_write_pre_commit_configs_returns_error_messages(
    language_support_service: LanguageSupportService,
    mock_open: MagicMock,
):
    mock_open.side_effect = Exception("error")
    mock_language = "CoolLang"
    mock_filename = "cool-lint-config.yml"
    result = language_support_service._write_pre_commit_configs(
        [
            LinterConfig(
                language=mock_language,
                linter_data=[LinterConfigData(filename=mock_filename, settings={})],
            ),
        ]
    )

    mock_open.assert_called_once()
    mock_open.return_value.write.assert_not_called()
    assert result == LinterConfigWriteResult(
        error_messages=[
            f"Failed to write {mock_filename} linter config file for {mock_language}"
        ],
        successful_languages=[],
    )


def test_write_pre_commit_configs_handles_empty_lint_configs(
    language_support_service: LanguageSupportService,
    mock_open: MagicMock,
):
    result = language_support_service._write_pre_commit_configs([])

    mock_open.assert_not_called()
    mock_open.return_value.write.assert_not_called()
    assert result == LinterConfigWriteResult(
        error_messages=[],
        successful_languages=[],
    )

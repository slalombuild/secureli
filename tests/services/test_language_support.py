from unittest.mock import MagicMock

import pytest
from pytest_mock import MockerFixture

from secureli.abstractions.pre_commit import (
    InstallResult,
)
from secureli.services.language_support import LanguageSupportService
from secureli.services.language_config import (
    LanguageConfigService,
    LanguagePreCommitResult,
    LoadLinterConfigsResult,
)


@pytest.fixture()
def mock_open_config(mocker: MockerFixture) -> MagicMock:
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


# def test_that_language_support_attempts_to_install_pre_commit_hooks(
#     language_support_service: LanguageSupportService,
#     mock_language_config_service: MagicMock,
#     mock_data_loader: MagicMock,
#     mock_open: MagicMock,
#     mock_pre_commit_hook: MagicMock,
# ):
#     def mock_loader_side_effect(resource):
#         return """
#             http://sample-repo.com/baddie-finder:
#                 - baddie-finder
#         """
#
#     mock_language_config_service.get_language_config.return_value = LanguagePreCommitResult(
#         language="Python",
#         version="abc123",
#         linter_config=LoadLinterConfigsResult(successful=True, linter_data=list({"key": {"example"}})),
#         config_data="""
#             repos:
#             -   repo: http://sample-repo.com/baddie-finder
#                 hooks:
#                 -    id: baddie-finder
#             """,
#     )
#
#     mock_data_loader.side_effect = mock_loader_side_effect
#
#     metadata = language_support_service.apply_support(["RadLang"])
#
#     # mock_pre_commit_hook.install.assert_called_once()
#     assert metadata.security_hook_id == "baddie-finder"


def test_that_language_support_calculates_version_for_language(
    language_support_service: LanguageSupportService,
    mock_language_config_service: MagicMock,
):
    mock_language_config_service.get_language_config.return_value = LanguagePreCommitResult(
        language="Python",
        version="abc123",
        linter_config=LoadLinterConfigsResult(successful=False, linter_data=list()),
        config_data="""
            repos:
            -   repo: http://sample-repo.com/baddie-finder
                hooks:
                -    id: baddie-finder
            """,
    )

    version = language_support_service.version_for_language(["RadLang"])

    mock_language_config_service.get_language_config.assert_called_with("base")
    assert version is not None


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


def test_that_get_current_config_returns_config_data(
    language_support_service: LanguageSupportService, mock_open_config: MagicMock
):
    config = language_support_service.get_current_configuration()

    assert config["exclude"] == "some-exclude-regex"


#### validate_config #####
def test_that_validate_config_returns_no_output_on_config_match(
    language_support_service: LanguageSupportService,
    mock_language_config_service: MagicMock,
    mock_open_config: MagicMock,
    mock_hashlib: MagicMock,
):
    config_data = """
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

    mock_language_config_service.get_language_config.return_value = (
        LanguagePreCommitResult(
            language="Python",
            version="mock-hash-code",
            linter_config=LoadLinterConfigsResult(successful=False, linter_data=list()),
            config_data=config_data,
        )
    )

    validation_result = language_support_service.validate_config(["Python"])

    assert validation_result.successful
    assert validation_result.output == ""


def test_that_validate_config_detects_mismatched_configs(
    language_support_service: LanguageSupportService,
    mock_language_config_service: MagicMock,
    mock_open_config: MagicMock,
):
    mock_language_config_service.get_language_config.return_value = LanguagePreCommitResult(
        language="Python",
        version="abc123",
        linter_config=LoadLinterConfigsResult(successful=False, linter_data=list()),
        config_data='{"exclude": "some-exclude-regex","repos":[{"hooks":[{"id":"some-test-hook"}],"repo":"xyz://some-test-repo-url","rev":"1.0.1"}]}',
    )
    validation_result = language_support_service.validate_config(["Python"])

    assert not validation_result.successful


def test_that_validate_config_detects_mismatched_hook_versions(
    language_support_service: LanguageSupportService,
    mock_hashlib_no_match: MagicMock,
    mock_language_config_service: MagicMock,
    mock_open_config: MagicMock,
):
    config_value = """
    exclude: some-exclude-regex
    repos:
    - hooks:
      - id: some-test-hook
      repo: xyz://some-test-repo-url
      rev: 1.0.1
    - hooks:
      - id: some-other-test-hook
      repo: xyz://some-other-test-repo-url
      rev: 1.0.0
    """

    mock_language_config_service.get_language_config.return_value = (
        LanguagePreCommitResult(
            language="Python",
            version="abc123",
            linter_config=LoadLinterConfigsResult(successful=False, linter_data=list()),
            config_data=config_value,
        )
    )

    validation_result = language_support_service.validate_config(["Python"])
    output_by_line = validation_result.output.splitlines()

    assert (
        output_by_line[-1]
        == "Expected xyz://some-test-repo-url to be rev 1.0.1 but it is configured to rev 1.0.0"
    )


def test_that_validate_config_detects_extra_repos(
    language_support_service: LanguageSupportService,
    mock_hashlib_no_match: MagicMock,
    mock_language_config_service: MagicMock,
    mock_open_config: MagicMock,
):
    def mock_side_effect(resource: str):
        config_value = """
        exclude: some-exclude-regex
        repos:
        - hooks:
          - id: some-test-hook
          repo: xyz://some-test-repo-url
          rev: 1.0.0
        """
        if resource == "base":
            config_value = """"""

        return LanguagePreCommitResult(
            language="Python",
            version="abc123",
            linter_config=LoadLinterConfigsResult(successful=False, linter_data=list()),
            config_data=config_value,
        )

    mock_language_config_service.get_language_config.side_effect = mock_side_effect

    validation_result = language_support_service.validate_config(["Python"])
    output_by_line = validation_result.output.splitlines()

    assert output_by_line[-3] == "Found unexpected repos in .pre-commit-config.yaml:"
    assert output_by_line[-2] == "- xyz://some-other-test-repo-url"


def test_that_validate_config_detects_missing_repos(
    language_support_service: LanguageSupportService,
    mock_hashlib_no_match: MagicMock,
    mock_language_config_service: MagicMock,
    mock_open_config: MagicMock,
):
    def mock_side_effect(resource: str):
        config_value = """
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
        if resource == "base":
            config_value = """
            repos:
            - hooks:
              - id: some-third-test-hook
              repo: xyz://some-third-test-repo-url
              rev: 1.0.0
            """

        return LanguagePreCommitResult(
            language="Python",
            version="abc123",
            linter_config=LoadLinterConfigsResult(successful=False, linter_data=list()),
            config_data=config_value,
        )

    mock_language_config_service.get_language_config.side_effect = mock_side_effect

    validation_result = language_support_service.validate_config(["Python"])
    output_by_line = validation_result.output.splitlines()

    assert (
        output_by_line[-4]
        == "Some expected repos were misssing from .pre-commit-config.yaml:"
    )
    assert output_by_line[-3] == "- xyz://some-third-test-repo-url"


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
            linter_data=[{"key": {"example"}}],
        ),
        config_data="""
            repos:
            -   repo: http://sample-repo.com/baddie-finder
                hooks:
                -    id: baddie-finder
            """,
    )

    mock_data_loader.side_effect = mock_loader_side_effect

    metadata = language_support_service.apply_support(["RadLang"])

    # mock_pre_commit_hook.install.assert_called_once()
    assert metadata.security_hook_id == "baddie-finder"


# def test_that_language_support_handles_malformed_config_and_does_not_write(
#     language_support_service: LanguageSupportService,
#     mock_language_config_service: MagicMock,
#     mock_data_loader: MagicMock,
#     mock_open: MagicMock,
#     mock_pre_commit_hook: MagicMock,
# ):
#     def mock_loader_side_effect(resource):
#         return """
#             http://sample-repo.com/baddie-finder:
#                 - baddie-finder
#         """
#
#     mock_language_config_service.get_language_config.return_value = LanguagePreCommitResult(
#         language="Python",
#         version="abc123",
#         linter_config=LoadLinterConfigsResult(
#             successful=True,
#             linter_data=["boo config"],
#         ),
#         config_data="""
#             repos:
#             -   repo: http://sample-repo.com/baddie-finder
#                 hooks:
#                 -    id: baddie-finder
#             """,
#     )
#
#     mock_data_loader.side_effect = mock_loader_side_effect
#
#     metadata = language_support_service.apply_support(["RadLang"])
#
#     mock_pre_commit_hook.install.assert_called_once()
#     assert metadata.security_hook_id == "baddie-finder"

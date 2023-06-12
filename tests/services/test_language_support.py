from unittest.mock import MagicMock

import pytest

from secureli.abstractions.pre_commit import (
    InstallResult,
    LanguagePreCommitConfigInstallResult,
)
from secureli.services.language_support import LanguageSupportService


@pytest.fixture()
def mock_pre_commit_config_install() -> MagicMock:
    mock_pre_commit_config_install_result = LanguagePreCommitConfigInstallResult(
        num_non_success=0, num_non_success=0, non_success_messages=list()
    )

    return mock_pre_commit_config_install_result


@pytest.fixture()
def mock_pre_commit_hook() -> MagicMock:
    mock_pre_commit_hook = MagicMock()
    mock_pre_commit_hook.version_for_language.return_value = "abc123"
    mock_pre_commit_hook.install.return_value = InstallResult(
        successful=True,
        version_installed="abc123",
        configs_result=mock_pre_commit_config_install(),
    )
    mock_pre_commit_hook.secret_detection_hook_id.return_value = "baddie-finder"
    return mock_pre_commit_hook


@pytest.fixture()
def mock_git_ignore() -> MagicMock:
    mock_git_ignore = MagicMock()
    return mock_git_ignore


@pytest.fixture()
def language_support_service(
    mock_pre_commit_hook: MagicMock,
    mock_git_ignore: MagicMock,
) -> LanguageSupportService:
    return LanguageSupportService(
        pre_commit_hook=mock_pre_commit_hook,
        git_ignore=mock_git_ignore,
    )


def test_that_language_support_attempts_to_install_pre_commit_hooks(
    language_support_service: LanguageSupportService,
    mock_pre_commit_hook: MagicMock,
):
    metadata = language_support_service.apply_support("RadLang")

    mock_pre_commit_hook.install.assert_called_once_with("RadLang")
    assert metadata.security_hook_id == "baddie-finder"


def test_that_language_support_calculates_version_for_language(
    language_support_service: LanguageSupportService,
    mock_pre_commit_hook: MagicMock,
):
    version = language_support_service.version_for_language("RadLang")

    mock_pre_commit_hook.version_for_language.assert_called_once_with("RadLang")
    assert version == "abc123"

from dependency_injector import containers, providers

from secureli.modules.shared.abstractions.echo import TyperEcho
from secureli.modules.shared.abstractions.lexer_guesser import PygmentsLexerGuesser
from secureli.modules.shared.abstractions.pre_commit import PreCommitAbstraction
from secureli.actions.action import ActionDependencies
from secureli.actions.initializer import InitializerAction
from secureli.actions.scan import ScanAction
from secureli.actions.build import BuildAction
from secureli.actions.update import UpdateAction
from secureli.modules.shared.abstractions.repo import GitRepo
from secureli.repositories.repo_files import RepoFilesRepository
from secureli.repositories.secureli_config import SecureliConfigRepository
from secureli.repositories.repo_settings import SecureliRepository
from secureli.modules.shared.resources import read_resource
from secureli.modules import language_analyzer
from secureli.modules.observability.observability_services.logging import LoggingService
from secureli.modules.core.core_services.scanner import HooksScannerService
from secureli.modules.core.core_services.updater import UpdaterService
from secureli.modules.pii_scanner.pii_scanner import PiiScannerService
from secureli.modules.secureli_ignore import SecureliIgnoreService
from secureli.settings import Settings


class Container(containers.DeclarativeContainer):
    """
    Arrange various dependencies and instruct the system on how to wire them up.
    """

    """The secureli input configuration, which drives how secureli performs its tasks"""
    config = providers.Configuration()

    """Data for the 'build' command, as drawn from the resources"""
    build_data = providers.Callable(read_resource, resource_name="build.txt")

    settings = providers.Factory(Settings)

    secureli_ignored_file_patterns = providers.Factory(
        SecureliIgnoreService,
        settings,
    )().ignored_file_patterns()

    git_ignored_file_patterns = providers.Factory(
        language_analyzer.git_ignore.GitIgnoreService
    )().ignored_file_patterns()

    combined_ignored_file_patterns = list(
        set(secureli_ignored_file_patterns + git_ignored_file_patterns)
    )

    # Repositories

    """Loads files from the repository folder, filtering out invisible files"""
    repo_files_repository = providers.Factory(
        RepoFilesRepository,
        max_file_size=config.repo_files.max_file_size.as_int(),
        ignored_file_extensions=config.repo_files.ignored_file_extensions,
        ignored_file_patterns=combined_ignored_file_patterns,
    )

    """
    Loads and saves the seCureLI output configuration, which stores the outcomes of
    running init and other derived data.
    """
    secureli_config_repository = providers.Factory(SecureliConfigRepository)

    settings_repository = providers.Factory(SecureliRepository)

    # Abstractions

    """The echo service, used to stylistically render text to the terminal"""
    echo = providers.Factory(
        TyperEcho,
        level=config.echo.level,
    )

    """Guesses the lexer within a given file"""
    lexer_guesser = providers.Factory(PygmentsLexerGuesser)

    """Wraps the execution and management of pre-commit in our consuming repo"""
    pre_commit_abstraction = providers.Factory(
        PreCommitAbstraction,
        command_timeout_seconds=config.language_support.command_timeout_seconds,
        echo=echo,
    )

    """Wraps the execution and management of git commands"""
    git_repo = providers.Factory(GitRepo)

    # Services

    """Analyzes a set of files to try to determine the most common languages"""

    """
    Manages the repository's git ignore file, making sure secureli-managed
    files are ignored
    """
    git_ignore_service = providers.Factory(
        language_analyzer.git_ignore.GitIgnoreService
    )

    language_config_service = providers.Factory(
        language_analyzer.language_config.LanguageConfigService,
        data_loader=read_resource,
        command_timeout_seconds=config.language_support.command_timeout_seconds,
        ignored_file_patterns=secureli_ignored_file_patterns,
    )

    """Identifies the configuration version for the language and installs it"""
    language_support_service = providers.Factory(
        language_analyzer.language_support.LanguageSupportService,
        pre_commit_hook=pre_commit_abstraction,
        git_ignore=git_ignore_service,
        language_config=language_config_service,
        data_loader=read_resource,
        echo=echo,
    )

    """Analyzes a given repo to try to identify the most common language"""
    language_analyzer_service = providers.Factory(
        language_analyzer.language_analyzer.LanguageAnalyzerService,
        repo_files=repo_files_repository,
        lexer_guesser=lexer_guesser,
    )

    """Logs branch-level secureli log entries to the disk"""
    logging_service = providers.Factory(
        LoggingService,
        language_support=language_support_service,
        secureli_config=secureli_config_repository,
    )

    """The service that scans the repository using pre-commit configuration"""
    hooks_scanner_service = providers.Factory(
        HooksScannerService,
        pre_commit=pre_commit_abstraction,
    )

    """The service that scans the repository for potential PII"""
    pii_scanner_service = providers.Factory(
        PiiScannerService,
        repo_files=repo_files_repository,
        echo=echo,
    )

    updater_service = providers.Factory(
        UpdaterService,
        pre_commit=pre_commit_abstraction,
        config=secureli_config_repository,
    )

    # Actions

    action_deps = providers.Factory(
        ActionDependencies,
        echo=echo,
        language_analyzer=language_analyzer_service,
        language_support=language_support_service,
        hooks_scanner=hooks_scanner_service,
        secureli_config=secureli_config_repository,
        settings=settings_repository,
        updater=updater_service,
    )

    """The Build Action, used to render the build_data using the echo"""
    build_action = providers.Factory(
        BuildAction,
        build_data=build_data,
        echo=echo,
        logging=logging_service,
    )

    """Initializer Action, representing what happens when the init command is invoked"""
    initializer_action = providers.Factory(
        InitializerAction,
        action_deps=action_deps,
        logging=logging_service,
    )

    """Scan Action, representing what happens when the scan command is invoked"""
    scan_action = providers.Factory(
        ScanAction,
        action_deps=action_deps,
        echo=echo,
        logging=logging_service,
        hooks_scanner=hooks_scanner_service,
        pii_scanner=pii_scanner_service,
        git_repo=git_repo,
    )

    """Update Action, representing what happens when the update command is invoked"""
    update_action = providers.Factory(
        UpdateAction,
        action_deps=action_deps,
        echo=echo,
        logging=logging_service,
        updater=updater_service,
    )

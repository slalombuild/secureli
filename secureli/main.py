from pathlib import Path
from typing import Optional, List
from typing_extensions import Annotated
import typer
from typer import Option

from secureli.actions.setup import SetupAction
from secureli.container import Container
from secureli.modules.shared.models.echo import Color
from secureli.modules.shared.models.install import VerifyOutcome
from secureli.modules.shared.models.publish_results import PublishResultsOption
from secureli.modules.shared.models.scan import ScanMode
from secureli.modules.shared.resources import read_resource
from secureli.settings import Settings
import secureli.repositories.secureli_config as SecureliConfig
from secureli.modules.shared.utilities import secureli_version

# Create SetupAction outside of DI, as it's not yet available.
setup_action = SetupAction(epilog_template_data=read_resource("epilog.md"))
app = typer.Typer(
    no_args_is_help=True, rich_markup_mode="rich", epilog=setup_action.create_epilog()
)

container = Container()
container.config.from_pydantic(Settings())


def version_callback(value: bool):
    if value:
        typer.echo(secureli_version())
        pre_commit_abstr = container.pre_commit_abstraction()
        path = Path(".")

        if pre_commit_abstr.pre_commit_config_exists(path):
            typer.echo("\nHook Versions:")
            typer.echo("--------------")
            config = pre_commit_abstr.get_pre_commit_config(path)

            all_repos = [
                (hook.id, repo.rev.lstrip("v") if repo.rev else None)
                for repo in config.repos
                for hook in repo.hooks
            ]

            sorted_repos = sorted(all_repos, key=lambda x: x[0])

            for hook_id, version in sorted_repos:
                typer.echo(f"{hook_id:<30} {version}")

        raise typer.Exit()


@app.callback()
def setup(
    version: Annotated[
        Optional[bool],
        Option("--version", "-v", callback=version_callback, is_eager=True),
    ] = None,
):
    """
    seCureLI:
    Secure Project Manager :sparkles:
    ---
    An intelligent CLI that helps developers build securely
    """
    # Initializes the DI container for each command
    container.init_resources()
    container.wire(modules=[__name__])


@app.command()
def init(
    reset: bool = Option(
        False,
        "--reset",
        "-r",
        help="Disregard the installed configuration, if any, and treat as a new install",
    ),
    yes: bool = Option(
        False,
        "--yes",
        "-y",
        help="Say 'yes' to every prompt automatically without input",
    ),
    directory: Annotated[
        Path,
        Option(
            ".",
            "--directory",
            "-d",
            help="Run secureli against a specific directory",
        ),
    ] = Path("."),
):
    """
    Detect languages and initialize pre-commit hooks and linters for the project
    """
    SecureliConfig.FOLDER_PATH = Path(directory)

    init_result = container.initializer_action().initialize_repo(
        Path(directory), reset, yes
    )
    if init_result.outcome in [
        VerifyOutcome.UP_TO_DATE,
        VerifyOutcome.UPDATE_SUCCEEDED,
    ]:
        update()


@app.command()
def scan(
    mode: ScanMode = Option(
        ScanMode.STAGED_ONLY,
        "--mode",
        "-m",
        help="Scan the files you're about to commit (the default) or all files in the repo.",
    ),
    publish_results: PublishResultsOption = Option(
        "never",
        help="When to publish the results of the scan to the configured observability platform",
    ),
    specific_test: Optional[str] = Option(
        None,
        "--specific-test",
        "-t",
        help="Limit the scan to a specific hook ID from your pre-commit config",
    ),
    directory: Annotated[
        Path,
        Option(
            ".",
            "--directory",
            "-d",
            help="Run secureli against a specific directory",
        ),
    ] = Path("."),
    files: List[str] = Option(
        None,
        "--file",
        "-f",
        help="""
            Run secureli scan against a specific file/folder.
            This can be included multiple times to scan multiple files e.g '--file file1 --file file2'
        """,
    ),
):
    """
    Performs an explicit check of the repository to detect security issues without remote logging.
    """
    SecureliConfig.FOLDER_PATH = Path(directory)
    container.scan_action().scan_repo(
        folder_path=Path(directory),
        scan_mode=mode,
        always_yes=False,
        publish_results_condition=publish_results,
        specific_test=specific_test,
        files=files,
    )


@app.command(hidden=True)
def build(color: Color = Color.BLUE):
    """
    (Easter Egg) Arrange a visit with our fearless security leader!
    """
    container.build_action().print_build(color)


@app.command()
def update(
    latest: bool = Option(
        False,
        "--latest",
        "-l",
        help="Update the installed pre-commit hooks to their latest versions",
    ),
    directory: Annotated[
        Path,
        Option(
            ".",
            "--directory",
            "-d",
            help="Run secureli against a specific directory",
        ),
    ] = Path("."),
):
    """
    Update linters, configuration, and all else needed to maintain a secure repository.
    """
    SecureliConfig.FOLDER_PATH = Path(directory)
    container.update_action().update_hooks(Path(directory), latest)


if __name__ == "__main__":
    app()

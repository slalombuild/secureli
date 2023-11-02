from pathlib import Path
from typing import Optional
from typing_extensions import Annotated
import typer
from typer import Option

from secureli.actions.scan import ScanMode
from secureli.actions.setup import SetupAction
from secureli.container import Container
from secureli.abstractions.echo import Color
from secureli.resources import read_resource
from secureli.settings import Settings
import secureli.repositories.secureli_config as SecureliConfig
from secureli.utilities.secureli_meta import secureli_version

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
        Optional[Path],
        Option(
            ".",
            "--directory",
            "-d",
            help="Run secureli against a specific directory",
        ),
    ] = ".",
):
    """
    Detect languages and initialize pre-commit hooks and linters for the project
    """
    SecureliConfig.FOLDER_PATH = Path(directory)
    container.initializer_action().initialize_repo(Path(directory), reset, yes)
    update()


@app.command()
def scan(
    yes: bool = Option(
        False,
        "--yes",
        "-y",
        help="Say 'yes' to every prompt automatically without input",
    ),
    mode: ScanMode = Option(
        ScanMode.STAGED_ONLY,
        "--mode",
        "-m",
        help="Scan the files you're about to commit (the default) or all files in the repo.",
    ),
    specific_test: Optional[str] = Option(
        None,
        "--specific-test",
        "-t",
        help="Limit the scan to a specific hook ID from your pre-commit config",
    ),
    directory: Annotated[
        Optional[Path],
        Option(
            ".",
            "--directory",
            "-d",
            help="Run secureli against a specific directory",
        ),
    ] = ".",
):
    """
    Performs an explicit check of the repository to detect security issues without remote logging.
    """
    SecureliConfig.FOLDER_PATH = Path(directory)
    container.scan_action().scan_repo(Path(directory), mode, yes, specific_test)


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
        Optional[Path],
        Option(
            ".",
            "--directory",
            "-d",
            help="Run secureli against a specific directory",
        ),
    ] = ".",
):
    """
    Update linters, configuration, and all else needed to maintain a secure repository.
    """
    SecureliConfig.FOLDER_PATH = Path(directory)
    container.update_action().update_hooks(Path(directory), latest)


if __name__ == "__main__":
    app()

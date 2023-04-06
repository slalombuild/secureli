# SeCureLI

# Environment Requirements

## Mac Only (for now!)

Note that, as of today, this repo is being built on and tested against macOS 12.6 Monterey. Windows support will be coming soon™.

## Supported Languages
SeCureLI has Slalom-maintained templates for security management of the following languages.
- C# .Net
- Java
- Python
- Terraform
- TypeScript

## Planned Languages
SeCureLI is currently in alpha, with support for additional languages planned, including:
- JavaScript

## Python 3.9.9

This repo was started against Python 3.9.9, which released 11/15/2021. Security support will last until 10/05/2025. Newer versions should be fine, older versions will likely not work.

## C Compiler

Certain dependencies are implemented as C extensions. Under certain circumstances, you may need to compile the package from sources on your machine. You’ll need a C compiler and Python header files, such as Xcode and Xcode’s command line tools for the Mac, if this is the case. Generally you’ll be guided through this process as you attempt to resolve dependencies (see `poetry install` below).

Do no setup for this requirement unless prompted to do so, and then follow the instructions given.

# Cloning the Repo and Setup

- Install Homebrew if needed
  - https://brew.sh
  - Run these three commands (or something like them) in your terminal to add Homebrew to your PATH:

```commandline
    echo '# Set PATH, MANPATH, etc., for Homebrew.' >> /Users/tristanl/.zprofile
    echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> /Users/tristanl/.zprofile
    eval "$(/opt/homebrew/bin/brew shellenv)"
```

- Using Homebrew, install python if needed (installs 3.9.6 as of 11/04/2022)
  - `brew install python`
- Install [Poetry](https://python-poetry.org/docs/)
  - Troubleshooting: If you get an error about python and virtual environments, and you have just installed python using Homebrew, you may need to close and relaunch your terminal
  - Similar to the next steps in the homebrew section, follow the instructions to register Poetry with your PATH, running something like the following:

```commandline
echo '# Add Poetry bin directory to the PATH' >> /Users/tristanl/.zprofile
echo 'export PATH="/Users/tristanl/.local/bin:$PATH"' >> /Users/tristanl/.zprofile
source ~/.zprofile
```

- Install [PyCharm Community Edition](https://www.jetbrains.com/pycharm/download/#section=mac)
  - Launch PyCharm and create a new sample project
  - Use the Tools menu and select `Create Command-line Launcher...`
    - Troubleshooting: You may need to create a new project in order to see the Tools menu
  - Perform a one-time configuration of Poetry into PyCharm. Follow the instructions on PyCharm’s website
    - [https://www.jetbrains.com/help/pycharm/poetry.html](https://www.jetbrains.com/help/pycharm/poetry.html)
- Clone the repo
  - `git clone git@bitbucket.org:slalom-consulting/secureli.git`
  - `cd secureli`
- Activate a virtual environment using Poetry
  - `poetry shell`
  - This will activate a new virtual environment, and PyCharm should automatically pick this up.
    - To leave this virtual environment, use `exit`, not `deactivate`
- Install your dependencies with Poetry
  - `poetry install`
- Open the new repo with PyCharm
  - `charm .` (assuming you set up the Command-line Launcher above 👆)
  - Say “OK” when prompted to create a poetry environment using pyproject.toml
- From the terminal, either in PyCharm or in the OS Terminal, type `secureli` and press Enter. You should see SeCureLI’s documentation appear, with a list of supported commands.
- Run the tests
  - `pytest`
- Calculate code coverage
  - `coverage run -m pytest && coverage html`
  - Open the `htmlcov/index.html` file to view your coverage report
- Try it out!
  - With the virtual environment still activated, and having installed (i.e. `poetry shell && poetry install`), run `secureli` and check out the Usage instructions
  - Right now, all it does is try to determine what the language is of the repo

## Create your first Run/Debug Configuration

- At the top-right of the PyCharm window, select the dropdown for managing Run/Debug configurations (it should say “Current File”) and choose “Edit Configurations…”
  - Add a new “Python” run configuration
  - Enter “Init” as the name
  - For Script path, type `secureli/main.py`
  - For Parameters, type `init`
  - For Working directory, use the file browser to select the outer “secureli” folder, NOT the inner folder.
    - **Bad** Example: /Users/tristan/Development/secureli**/secureli/**
    - **Good** Example: /Users/tristan/Development/secureli/
    - It will appear as an absolute path, but hopefully should be relative for others
  - Hit “OK” to save and select your first Run/Debug configuration

## Testing your Init Configuration

- Hit the triangle-shaped Run button next to the dropdown, which should say “Init”
  - If it does not say “Init”, select it in the dropdown
- This should display terminal output within PyCharm that looks like the following:

```jsx
/secureli-LF8LGRWE-py3.9/bin/python secureli/main.py init
SeCureLI has not been setup yet. Initialize SeCureLI now? [Y/n]:
```

This is a working prompt. If this is your first time running this, answer “Y” (or just press enter) and you’ll install SeCureLI for SeCureLI! It should detect the python repo and setup your pre-commit hooks. Your output should look like this:

```commandline
% secureli/main.py init
SeCureLI has not been setup yet. Initialize SeCureLI now? [Y/n]: Y
Detected the following languages:
- Python: 93%
- YAML: 7%
Overall Detected Language: Python
Installing support for Python
pre-commit installed at .git/hooks/pre-commit
Python pre-commit checks installed successfully
```

Running Init a second time should detect that the repo is configured and up-to-date:

```python
/secureli-LF8LGRWE-py3.9/bin/python secureli/main.py init
Already installed for Python language and up to date
```

## Creating the remaining Run/Debug Configurations

- Click the Run/Debug Configuration, which should show “Init” as the selected configuration, and choose “Edit Configurations…”
- With the “Init” configuration shown in the list view on the left, click the Copy Configuration button (or hit Command-D on your keyboard) four times to create four copies of the configuration
- Leaving the original “Init” configuration untouched, adjust the four copies with the following contents:
  - Name: Scan
    - Parameters: `scan`
  - Name: Update
    - Parameters: `update`
  - Name: Yeti
    - Parameters: `yeti`
- Test each of these configurations and see that the expected “not yet implemented” message is shown

# Usage

Once installed, whether by cloning and setting up the repo in a virtual environment or by installing it via brew (future state), you can see the latest documentation for SeCureLI by entering the following on a command prompt:

```python
% secureli --help
```

You will see a list of commands and descriptions of each. You can also pull up documentation for each command with the same pattern. For example:

```python
(secureli-py3.9) tristan@Tristans-MacBook-Pro secureli % secureli init --help

 Usage: secureli init [OPTIONS]

 Detect languages and initialize pre-commit hooks and linters for the project

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────╮
│ --reset  -r        Disregard the installed configuration, if any, and treat as a new install   │
│ --yes    -y        Say 'yes' to every prompt automatically without input                       │
│ --help             Show this message and exit.                                                 │
╰────────────────────────────────────────────────────────────────────────────────────────────────╯
```

When invoking these commands, you can combine the short versions into a single flag. For example, the following commands are equivalent:

```python
% secureli init --reset --yes
% secureli init -ry
```

# Configuration

SeCureLI is configurable via a .secureli.yaml file present in the consuming repository.

## .secureli.yaml - top level

| Key                | Description                                                                                                                      |
|--------------------|----------------------------------------------------------------------------------------------------------------------------------|
| `repo_files`       | Affects how SeCureLI will interpret the repository, both for language analysis and as it executes various linters.               |
| `echo`             | Adjusts how SeCureLI will print information to the user.                                                                         |
| `language_support` | Affects SeCureLI's language analysis and support phase.                                                                          |
| `pre_commit`       | Enables various overrides and options for SeCureLI's configuration and usage of pre-commit, the underlying code analysis system. |

## .secureli.yaml - repo_files

| Key                       | Description                                                                                                                                                                                                                                                             |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `max_file_size`           | A number in bytes. Files over this size will not be considered during language analysis, for speed purposes. Default: 100000                                                                                                                                            |
| `ignored_file_extensions` | Which file extensions not to consider during language analysis.                                                                                                                                                                                                         |
| `exclude_file_patterns`   | Which file patterns to ignore during language analysis and code analysis execution. Use a typical file pattern you might find in a .gitignore file, such as `*.py` or `tests/`. Certain patterns you will have to wrap in double-quotes for the entry to be valid YAML. |

## .secureli.yaml - echo

| Key     | Description                                                                                                                                        |
|---------|----------------------------------------------------------------------------------------------------------------------------------------------------|
| `level` | The log level to display to the user. Defaults to ERROR, which includes `error` and `print` messages, without including warnings or info messages. |

## .secureli.yaml - pre_commit

| Key                | Description                                                                                                                                                                                                                               |
|--------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `repos`            | A set of template-based Pre-Commit Repos to configure with overrides, identified by URL. These override repo-configurations stored in the template, and attempting to modify a repo not configured into the template will have no effect. |
| `suppressed_repos` | A set of template-based Pre-Commit Repo URLs to completely remove from the final configuration. These remove repo configurations stored in the template, removing a repo not stored in the template will be ignored.                      |

## .secureli.yaml - pre_commit.repos

| Key                   | Description                                                                                                                                            |
|-----------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------|
| `url`                 | The identifying URL of the repo being leveraged by pre-commit, within which one or more hooks can be leveraged.                                        |
| `hooks`               | A set of hooks associated with the specified repository to override. See the next section for what we can configure there.                             |
| `suppressed_hook_ids` | A set of hook IDs to remove from the repository as configured within the template. Hook IDs not present in the template configuration will be ignored. |

## .secureli.yaml - pre_commit.repos.hooks

| Key                     | Description                                                                                                                                                                                                                                                                  |
|-------------------------|------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| `id`                    | The identifying string of the pre-commit hook to override.                                                                                                                                                                                                                   |
| `arguments`             | A set of arguments to provide to the pre-commit hook identified by `id`. These arguments overwrite any existing arguments.                                                                                                                                                   |
| `additional_args`       | A set of arguments to provide to the pre-commit hook identified by `id`. These arguments are appended after an existing arguments.                                                                                                                                           |
| `exclude_file_patterns` | A set of file patterns to provide to pre-commit to ignore for the purposes of this hook. Use a typical file pattern you might find in a .gitignore file, such as `*.py` or `tests/`. Certain patterns you will have to wrap in double-quotes for the entry to be valid YAML. |

# SeCureLI Architecture

![SeCureLI’s architecture, including actions, services, APIs and repositories. Oh, my!](images/secureli-architecture.png)

SeCureLI’s architecture, including actions, services, APIs and repositories. Oh, my!

## Main

The entry point of the application. The main module sets up the dependency injection container, validates the input via the Typer framework and identifies and executes a single action. Main is the only module in the system aware of the Container.

Unit tests of Main simply ensure that the Container is set up and leveraged to kick off Actions.

## Container

The container is where all potential dependencies are registered and wired up. Configuration is read here, and is fed into various objects as necessary. Though Main is the only module that is aware of the Container, the Container is aware of every Module.

Unit tests of the Container ensure that the various providers are validated and initialized. This helps prevent common mistakes where dependencies are manipulated but the Container’s wire-up code was not adjusted accordingly.

## Actions

Actions orchestrate other services and respond to user interactions with SeCureLI. One CLI command is handled by a single Action, and a single action only handles one command. They are one for one.

Unit tests of Actions are done with mock services and abstractions.

## Services

Services represent a single responsibility and some light interaction with other services. These can be simple, like the Echo Service, which enables the app’s actions and services to print output to the console. A complex service like the Language Analyzer Service leverages the Repo Files Repository, the Lexer Guesser and the Echo Service to analyze a repository's languages.

Services do not leverage 3rd Party or External Dependencies directly, not even the disk. Services may leverage other services as well as abstractions.

Unit tests of Services are done with mock services and abstractions.

## Abstractions

Abstractions are mini-services that are meant to encapsulate a 3rd-party dependency. This allows us to mock interfaces we don’t own easier than leveraging duck typing and magic mocks while testing our own logic. This also allows us to swap out the underlying dependency with less risk of disruption to our entire application.

Abstractions should ONLY provide this wrapping, and no other business logic, unless that business logic is part of the abstraction and leverages the abstraction itself (see `EchoAbstraction` for an example of this)

Please note: this can become unwieldy fast. If your CLI is to extensively leverage a large 3rd party dependency, and is unlikely to swap out this functionality, then it’s a judgment call of the author or team to not create an abstraction of this library. This author trusts your judgment and assures you that you will not be jailed or fined.

Unit tests of Abstractions are done with mock 3rd party dependencies, not the dependencies themselves!

## APIs & Repositories

Objects that provide **faithful** representation of the underlying system without additional business logic or opinions. This does not have to be an exhaustive implementation. In other words, if the API hosts 30 endpoints for Store CRUD operations, and you only need one (i.e. GET /stores), then you can implement the one. However, GET /stores will take a StoreRequest object and return a StoreResponse object (as defined by the Store API OpenAPI documentation).

Preferably, APIs and Repositories will surface entity objects that programmatically represent the underlying object, such as a Pydantic data model or a dataclass and NOT dictionaries!

**The API will not** decide to expose it as a class that takes a store name property and creates its own request that represents a store name search. That’s a service’s job.

**The API will not** apply caching behavior. That’s a service’s job.

**The API will not** orchestrate or chain multiple requests together. That’s a service’s job.

Hopefully you’re seeing a pattern here. At some point in an application, an object exists that faithfully represents a dependent system. One call to the API will be one HTTP request in terms derived from (preferably dictated by) the API itself, no exceptions.

Unit tests of APIs and repositories are done with mock 3rd party dependencies to ensure the translation logic of the API is working.

## Third Party Dependencies

Any library provided via PyPI should be considered a 3rd party library. Examples: Typer, Pygments, etc.

Third party dependencies **shall not be unit tested**, but efforts will be taken to unit test their consumers by mocking these dependencies. Traditionally, this will take the place of creating and leveraging Abstractions (see above).

### Dockerfiles
Docker is used in this project solely to provide an isolated environment for testing Secureli and testing other projects with Secureli. The process is:

- run the docker command to build it
- if it builds successfully, congrats you're done

The project assumes you have a functioning docker install. These have been tested with the Colima engine. There are commands built into the pyproject.toml file to run these dockerfile builds. To build one, run `poetry run poe docker-build-dockerfilename`.

Current Dockerfiles
- secureli_Dockerfile - builds secureli and runs the same tests and verifications as the cicd pipeline
- homebrew_Dockerfile: Designed to verify secureli functionality
  - installs Homebrew(linuxbrew) on a Debian images
  - taps our private secureli homebrew tap
  - installs Secureli
  - Checks out the public pip repo, inits secureli into the repo and runs a scan

## License

Copyright 2023 Slalom, Inc.

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

  [Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0)

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.

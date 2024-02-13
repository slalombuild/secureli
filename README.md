[![seCureLI Logo](https://repository-images.githubusercontent.com/606206029/aa43fa10-689b-4f8a-a6dc-2e9ed06d9e2d)](https://github.com/slalombuild/secureli)

<h1 align="center">seCureLI</h1>
<strong>The Builder's Security CLI</strong>

seCureLI is a tool that enables you to experience the delight of building products by helping you get ideas from your head into working software as frictionlessly as possible, in a reliable, secure, scalable, and observable way.

seCureLI:

- scans your local repo for secrets before you commit code to a remote repository
- installs linters based on the code of your project to support security and coding best practices
- configures all the hooks needed so you don’t have to

seCureLI isn’t a magic tool that makes things secure because you have it. It enables a lot of other tools that you could set up individually and helps you as a builder write better code.

Looking to contribute? Read our [CONTRIBUTING.md](https://github.com/slalombuild/secureli/blob/main/CONTRIBUTING.md)

# Installation

## Homebrew

To install seCureLI via homebrew, issue the following commands

```commandline
brew tap slalombuild/secureli
brew install secureli
```

## pip (Package Installer for Python)

To install seCureLI via pip, issue the following commands

```commandline
pip install secureli
```

# Usage

## Help

Once installed you can see the latest documentation for seCureLI by entering the following on a command prompt:

```bash
$ secureli --help
```

You will see a list of commands and descriptions of each. You can also pull up documentation for each command with the same pattern. For example:

```bash
$ secureli init --help

 Usage: secureli init [OPTIONS]

 Detect languages and initialize pre-commit hooks and linters for the project

╭─ Options ──────────────────────────────────────────────────────────────────────────────────────╮
│ --reset       -r      Disregard the installed configuration, if any, and treat as a new install   │
│ --yes         -y      Say 'yes' to every prompt automatically without input                       │
│ --directory .,-d PATH Run secureli against a specific directory [default: .]
│ --help                Show this message and exit.                                                 │
╰────────────────────────────────────────────────────────────────────────────────────────────────╯
```

When invoking these commands, you can combine the short versions into a single flag. For example, the following commands are equivalent:

```bash
% secureli init --reset --yes
% secureli init -ry
```

## Init

After seCureLI is installed, you can use it to configure your local git repository with a set of pre-commit hooks appropriate for your repo, based on the languages found in your repo's source code files.

All you need to do is run:

```bash
% secureli init
```

Running `secureli init` will allow seCureLI to detect the languages in your repo, install pre-commit, install all the appropriate pre-commit hooks for your local repo, run a scan for secrets in your local repo, and update the installed hooks.

# Upgrade

## Upgrading seCureLI via Homebrew

If you installed seCureLI using Homebrew, you can use the standard homebrew update command to pull down the latest formula.

```commandline
brew update
```

## Upgrading via pip

If you installed seCureLI using pip, you can use the following command to upgrade to the latest version of seCureLI.

```commandline
pip install --upgrade secureli
```

## Upgrading pre-commit hooks for repo

In order to upgrade to the latest released version of each pre-commit hook configured for your repo, use the following command.

```commandline
secureli update --latest
```

# Configuration

seCureLI is configurable via a .secureli.yaml file present in the root of your local repository.

## .secureli.yaml

### top level

| Key                | Description                                                                                                        |
| ------------------ | ------------------------------------------------------------------------------------------------------------------ |
| `repo_files`       | Affects how seCureLI will interpret the repository, both for language analysis and as it executes various linters. |
| `echo`             | Adjusts how seCureLI will print information to the user.                                                           |
| `language_support` | Affects seCureLI's language analysis and support phase.                                                            |
| `telemetry`        | Includes options for seCureLI telemetry/api logging                                                                |

### repo_files

| Key                       | Description                                                                                                                                                                                                                                                             |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `max_file_size`           | A number in bytes. Files over this size will not be considered during language analysis, for speed purposes. Default: 100000                                                                                                                                            |
| `ignored_file_extensions` | Which file extensions not to consider during language analysis.                                                                                                                                                                                                         |
| `exclude_file_patterns`   | Which file patterns to ignore during language analysis and code analysis execution. Use a typical file pattern you might find in a .gitignore file, such as `*.py` or `tests/`. Certain patterns you will have to wrap in double-quotes for the entry to be valid YAML. |

### echo

| Key     | Description                                                                                                                                        |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `level` | The log level to display to the user. Defaults to ERROR, which includes `error` and `print` messages, without including warnings or info messages. |

### telemetry

| Key       | Description                                                                                                                                                                              |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `api_url` | The url endpoint to post telemetry logs to. This value is an alternative to setting the url as an environment variable. Note: The environment variable will precede this setting value |

## Using Observability Platform to Show Secret Detection Statistics

seCureLI can send secret detection events to an observability platform, such as New Relic. Other platforms may also work, but have not been tested.
Should you need seCureLI to work with other platforms, please create a new issue in github, or contribute to the open source project.

### Steps for New Relic

- Assuming, seCureLI has been setup and installed, sign up to New Relic Log Platform https://docs.newrelic.com/docs/logs/log-api/introduction-log-api/
- Retrieve API_KEY and API_ENDPOINT from New Relic. API_ENDPOINT for New Relic should be https://log-api.newrelic.com/log/v1
- On your development machine, setup environment variable with variable name SECURELI_LOGGING_API_KEY and SECURELI_LOGGING_API_ENDPOINT. The endpoint can alternatively be added and commited to source control via the .secureli.yaml file.
- Once the above setup is complete, everytime seCureLI triggered, it should send a usage log to New Relic
- In New Relic, you can create a dashboard of metric to see the number of times secret was caught using query such as

```pre
FROM Log Select sum(failure_count_details.detect_secrets) as 'Caught Secret Count'
```

## License

Copyright 2024 Slalom, Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

[Apache 2.0 License](http://www.apache.org/licenses/LICENSE-2.0)

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

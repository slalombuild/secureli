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

## Table of Contents <!-- omit in toc -->

- [Installation](#installation)
  - [Homebrew](#homebrew)
  - [pip (Package Installer for Python)](#pip-package-installer-for-python)
- [Usage](#usage)
  - [Help](#help)
  - [Init](#init)
  - [Scan](#scan)
    - [Scanned Files](#scanned-files)
    - [PII Scan](#pii-scan)
  - [Supported Languages](#supported-languages)
- [Upgrade](#upgrade)
  - [Upgrading seCureLI via Homebrew](#upgrading-secureli-via-homebrew)
  - [Upgrading via pip](#upgrading-via-pip)
  - [Upgrading pre-commit hooks for repo](#upgrading-pre-commit-hooks-for-repo)
- [Configuration](#configuration)
  - [.secureli.yaml](#secureliyaml)
    - [top level](#top-level)
    - [repo\_files](#repo_files)
    - [echo](#echo)
    - [pii\_scanner](#pii_scanner)
    - [telemetry](#telemetry)
  - [pre-commit](#pre-commit)
    - [Custom pre-commit configuration](#custom-pre-commit-configuration)
    - [Passing arguments to pre-commit hooks](#passing-arguments-to-pre-commit-hooks)
  - [`.secureli/repo-config.yaml`](#securelirepo-configyaml)
  - [Using Observability Platform to Show Secret Detection Statistics](#using-observability-platform-to-show-secret-detection-statistics)
    - [Steps for New Relic](#steps-for-new-relic)
- [License](#license)


## Installation

### Homebrew

To install seCureLI via homebrew, issue the following commands

```commandline
brew tap slalombuild/secureli
brew install secureli
```

### pip (Package Installer for Python)

To install seCureLI via pip, issue the following commands

```commandline
pip install secureli
```

## Usage

### Help

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

### Init

After seCureLI is installed, you can use it to configure your local git repository with a set of pre-commit hooks appropriate for your repo, based on the languages found in your repo's source code files.

All you need to do is run:

```bash
% secureli init
```

Running `secureli init` will allow seCureLI to detect the languages in your repo, install pre-commit, install all the appropriate pre-commit hooks for your local repo, run a scan for secrets in your local repo, and update the installed hooks.

### Scan

To manually trigger a scan, run:

```bash
% secureli scan
```

This will run through all hooks and custom scans, unless a `--specific-test` option is used. The default is to scan staged files only. To scan all files instead, use the `--mode all-files` option.

#### Scanned Files

By default, seCureLI will only scan files that are staged for commit. If you want to scan a different set of files, you can use the `--file` parameter. You can specify multiple files by passing the parameter multiple times, e.g. `--file file1 --file file2`.

#### PII Scan

seCureLI utilizes its own PII scan, rather than using an existing pre-commit hook. To exclude a line from being flagged by the PII scanner, you can use a `disable-pii-scan` marker in a comment to disable the scan for that line.

```
test_var = "some dummy data I don't want scanned" # disable-pii-scan
```

### Supported Languages

seCureLI has Slalom-maintained templates for security management of the following languages.

- Java
- Python
- Terraform
- JavaScript
- TypeScript
- C#
- Swift
- Golang
- Kotlin

## Upgrade

### Upgrading seCureLI via Homebrew

If you installed seCureLI using Homebrew, you can use the standard homebrew update command to pull down the latest formula.

```commandline
brew update
```

### Upgrading via pip

If you installed seCureLI using pip, you can use the following command to upgrade to the latest version of seCureLI.

```commandline
pip install --upgrade secureli
```

### Upgrading pre-commit hooks for repo

In order to upgrade to the latest released version of each pre-commit hook configured for your repo, use the following command.

```commandline
secureli update --latest
```

## Configuration

### .secureli.yaml

seCureLI is configurable via a `.secureli.yaml` file present in the root of your local repository.

#### top level

| Key                | Description                                                                                                        |
|--------------------|--------------------------------------------------------------------------------------------------------------------|
| `repo_files`       | Affects how seCureLI will interpret the repository, both for language analysis and as it executes various linters. |
| `echo`             | Adjusts how seCureLI will print information to the user.                                                           |
| `language_support` | Affects seCureLI's language analysis and support phase.                                                            |
| `pii_scanner`      | Includes options for seCureLI's PII scanner                                                                        |
| `telemetry`        | Includes options for seCureLI telemetry/api logging                                                                |

#### repo_files

| Key                       | Description                                                                                                                                                                                                                                                             |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `max_file_size`           | A number in bytes. Files over this size will not be considered during language analysis, for speed purposes. Default: 100000                                                                                                                                            |
| `ignored_file_extensions` | Which file extensions not to consider during language analysis.                                                                                                                                                                                                         |
| `exclude_file_patterns`   | Which file patterns to ignore during language analysis and code analysis execution. Use a typical file pattern you might find in a .gitignore file, such as `*.py` or `tests/`. Certain patterns you will have to wrap in double-quotes for the entry to be valid YAML. |

#### echo

| Key     | Description                                                                                                                                        |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `level` | The log level to display to the user. Defaults to ERROR, which includes `error` and `print` messages, without including warnings or info messages. |

#### pii_scanner

| Key                  | Description                                                    |
|----------------------|----------------------------------------------------------------|
| `ignored_extensions` | The extensions of files to ignore in addition to the defaults. |

#### telemetry

| Key       | Description                                                                                                                                                                              |
| --------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `api_url` | The url endpoint to post telemetry logs to. This value is an alternative to setting the url as an environment variable. Note: The environment variable will precede this setting value |

### pre-commit

[pre-commit](https://pre-commit.com/) is used for configuring pre-commit hooks. The configuration file is `.secureli/.pre-commit-config.yaml`, relative to the root of your repo. For details on modifying this file, see the pre-commit documentation on [configuring hooks](https://pre-commit.com/#pre-commit-configyaml---hooks).

#### Custom pre-commit configuration

If there is a `.pre-commit-config` file in your root when you initialize seCureLI, it will be merged with the default configuration written to `.secureli/.pre-commit-config.yaml`.

#### Passing arguments to pre-commit hooks

Special care needs to be taken when passing arguments to pre-commit hooks in `.pre-commit-config.yaml`. In particular, if you're passing parameters which themselves take arguments, you must ensure that both the parameter and its arguments are separate items in the array.

Examples:

**BAD**

```yaml
- args:
  - --exclude-files *.md
```

This is an array with a single element, `["--exclude files *.md"]`. This probably won't work as you're expecting.

**GOOD**

```yaml
- args:
  - --exclude-files
  - *.md
```

This is an array where the parameter and its argument are separate items; `["--exclude files", "*.md"]`

**ALSO GOOD**
```yaml
- args: ["--exclude-files", "*.md"]
```

### `.secureli/repo-config.yaml`

This file is generated by seCureLI and contains the configuration for the repo.
It is not intended to be modified by the user. Running `secureli update` will
update this file with the latest configuration.

### Using Observability Platform to Show Secret Detection Statistics

seCureLI can send secret detection events to an observability platform, such as New Relic. Other platforms may also work, but have not been tested.
Should you need seCureLI to work with other platforms, please create a new issue in github, or contribute to the open source project.

#### Steps for New Relic

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

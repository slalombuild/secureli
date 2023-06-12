[![SeCureLI Logo](https://repository-images.githubusercontent.com/606206029/aa43fa10-689b-4f8a-a6dc-2e9ed06d9e2d)](https://github.com/slalombuild/secureli)

<h1 align="center">SeCureLI</h1>
<strong>The Builder's Security CLI</strong>

SeCureLI is a tool that enables you to experience the delight of building products by helping you get ideas from your head into working software as frictionlessly as possible, in a reliable, secure, scalable, and observable way.

SeCureLI:

- scans your local repo for secrets before you commit code to a remote repository
- installs linters based on the code of your project to support security and coding best practices
- configures all the hooks needed so you don’t have to

SeCureLI isn’t a magic tool that makes things secure because you have it. It enables a lot of other tools that you could set up individually and helps you as a builder write better code.

Looking to contribute? Read our [CONTRIBUTING.md](https://github.com/slalombuild/secureli/blob/main/CONTRIBUTING.md)

# Installation and Usage

## Secureli Installation via Homebrew

Current the only packaging tool that is supported for Secureli is Homebrew. To install secureli via homebrew, issue the following commands

```commandline
brew tap slalombuild/secureli
brew install secureli
```

## Upgrading Secureli via Homebrew

To update secureli, you can use the standard homebrew update command to pull down the latest formula

```commandline
brew update
```

# Usage

Once installed you can see the latest documentation for SeCureLI by entering the following on a command prompt:

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

# Tutorial to Use Observability Platform to Show Usage Statistics

This tutorial uses New Relic as the sample observability platform. Other platforms may also work, but have not been tested.
Should you need seCureLI to work with other platforms, please create a new issue in github, or contribute to the open source project.

## Steps

- Assuming, seCureLI has been setup and installed, sign up to New Relic Log Platform https://docs.newrelic.com/docs/logs/log-api/introduction-log-api/
- Retrieve API_KEY and API_ENDPOINT from New Relic. API_ENDPOINT for New Relic should be https://log-api.newrelic.com/log/v1
- On your development machine, setup environment variable with variable name API_KEY and API_ENDPOINT
- Once the above setup is complete, everytime seCureLI triggered, it should send a usage log to New Relic
- In New Relic, you can create a dashboard of metric to see the number of times secret was caught using query such as

```commandline
FROM Log Select sum(failure_count_details.detect_secrets) as 'Caught Secret Count'
```

# Configuration

SeCureLI is configurable via a .secureli.yaml file present in the consuming repository.

## .secureli.yaml - top level

| Key                | Description                                                                                                                      |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------- |
| `repo_files`       | Affects how SeCureLI will interpret the repository, both for language analysis and as it executes various linters.               |
| `echo`             | Adjusts how SeCureLI will print information to the user.                                                                         |
| `language_support` | Affects SeCureLI's language analysis and support phase.                                                                          |
| `pre_commit`       | Enables various overrides and options for SeCureLI's configuration and usage of pre-commit, the underlying code analysis system. |

## .secureli.yaml - repo_files

| Key                       | Description                                                                                                                                                                                                                                                             |
| ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `max_file_size`           | A number in bytes. Files over this size will not be considered during language analysis, for speed purposes. Default: 100000                                                                                                                                            |
| `ignored_file_extensions` | Which file extensions not to consider during language analysis.                                                                                                                                                                                                         |
| `exclude_file_patterns`   | Which file patterns to ignore during language analysis and code analysis execution. Use a typical file pattern you might find in a .gitignore file, such as `*.py` or `tests/`. Certain patterns you will have to wrap in double-quotes for the entry to be valid YAML. |

## .secureli.yaml - echo

| Key     | Description                                                                                                                                        |
| ------- | -------------------------------------------------------------------------------------------------------------------------------------------------- |
| `level` | The log level to display to the user. Defaults to ERROR, which includes `error` and `print` messages, without including warnings or info messages. |

## .secureli.yaml - pre_commit

| Key                | Description                                                                                                                                                                                                                               |
| ------------------ | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `repos`            | A set of template-based Pre-Commit Repos to configure with overrides, identified by URL. These override repo-configurations stored in the template, and attempting to modify a repo not configured into the template will have no effect. |
| `suppressed_repos` | A set of template-based Pre-Commit Repo URLs to completely remove from the final configuration. These remove repo configurations stored in the template, removing a repo not stored in the template will be ignored.                      |

## .secureli.yaml - pre_commit.repos

| Key                   | Description                                                                                                                                            |
| --------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `url`                 | The identifying URL of the repo being leveraged by pre-commit, within which one or more hooks can be leveraged.                                        |
| `hooks`               | A set of hooks associated with the specified repository to override. See the next section for what we can configure there.                             |
| `suppressed_hook_ids` | A set of hook IDs to remove from the repository as configured within the template. Hook IDs not present in the template configuration will be ignored. |

## .secureli.yaml - pre_commit.repos.hooks

| Key                     | Description                                                                                                                                                                                                                                                                  |
| ----------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `id`                    | The identifying string of the pre-commit hook to override.                                                                                                                                                                                                                   |
| `arguments`             | A set of arguments to provide to the pre-commit hook identified by `id`. These arguments overwrite any existing arguments.                                                                                                                                                   |
| `additional_args`       | A set of arguments to provide to the pre-commit hook identified by `id`. These arguments are appended after an existing arguments.                                                                                                                                           |
| `exclude_file_patterns` | A set of file patterns to provide to pre-commit to ignore for the purposes of this hook. Use a typical file pattern you might find in a .gitignore file, such as `*.py` or `tests/`. Certain patterns you will have to wrap in double-quotes for the entry to be valid YAML. |

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

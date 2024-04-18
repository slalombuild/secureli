import configparser
import hashlib
import os
from uuid import uuid4
import requests
import subprocess

from collections import Counter
from importlib.metadata import version
from typing import Optional

from secureli.modules.observability.consts import logging
from secureli.modules.shared.models.publish_results import PublishLogResult
from secureli.modules.shared.models.result import Result
from secureli.modules.shared.models.scan import ScanFailure, ScanResult
from secureli.settings import Settings


def combine_patterns(patterns: list[str]) -> Optional[str]:
    """
    Combines a set of patterns from pathspec into a single combined regex
    suitable for use in circumstances that require a broad matching, such as
    re.find_all or a pre-commit exclusion pattern.

    Calling this with an empty set of patterns will return None
    :param patterns: The pattern strings provided by pathspec to combine
    :return: a combined pattern containing the one or more patterns supplied, or None
    if no patterns were supplied
    """
    if not patterns:
        return None

    if len(patterns) == 1:
        return patterns[0]

    # Don't mutate the input
    ignored_file_patterns = patterns.copy()

    # Quick sanitization process. Ultimately we combine all the regexes into a single
    # entry, and all patterns are generated with a capture group with the same ID, which
    # is invalid. We need to make sure every capture group is unique to combine them
    # into a single expression. This is not my favorite.
    for i in range(0, len(ignored_file_patterns)):
        ignored_file_patterns[i] = str.replace(
            ignored_file_patterns[i], "ps_d", f"ps_d{i}"
        )
    combined_patterns = str.join("|", ignored_file_patterns)
    combined_ignore_pattern = f"^({combined_patterns})$"
    return combined_ignore_pattern


def convert_failures_to_failure_count(failure_list: list[ScanFailure]):
    """
    Convert a list of Failure ids to a list of individual failure count with underscore naming convention
    :param failure_list: a list of Failure Object
    """
    list_of_failure_ids = []

    for failure in failure_list:
        failure_id_underscore = failure.id.replace("-", "_")
        list_of_failure_ids.append(failure_id_underscore)

    failure_count_list = Counter(list_of_failure_ids)
    return failure_count_list


def current_branch_name() -> str:
    """Leverage the git HEAD file to determine the current branch name"""
    try:
        with open(".git/HEAD", "r") as f:
            content = f.readlines()
            for line in content:
                if line[0:4] == "ref:":
                    return line.partition("refs/heads/")[2].strip()
    except IOError:
        return "UNKNOWN"


def format_sentence_list(items: list[str]) -> str:
    """
    Formats a list of string values to a comma separated
    string for use in a sentence structure.
    :param items: list of strings to join
    :return string of joined values as a sentence comma list
    i.e. "x, y, and z" or "x and y"
    """
    if not items:
        return ""
    elif len(items) == 1:
        return items[0]
    and_separator = ", and " if len(items) > 2 else " and "
    return ", ".join(items[:-1]) + and_separator + items[-1]


def git_user_email() -> str:
    """Leverage the command prompt to derive the user's email address"""
    args = ["git", "config", "user.email"]
    completed_process = subprocess.run(args, stdout=subprocess.PIPE)
    output = completed_process.stdout.decode("utf8").strip()
    return output


def hash_config(config: str) -> str:
    """
    Creates an MD5 hash from a config string
    :return: A hash string
    """
    config_hash = hashlib.md5(config.encode("utf8"), usedforsecurity=False).hexdigest()

    return config_hash


def origin_url() -> str:
    """Leverage the git config file to determine the remote origin URL"""
    git_config_parser = configparser.ConfigParser()
    git_config_parser.read(".git/config")
    return (
        git_config_parser['remote "origin"'].get("url", "UNKNOWN", raw=True)
        if git_config_parser.has_section('remote "origin"')
        else "UNKNOWN"
    )


def post_log(log_data: str, settings: Settings) -> PublishLogResult:
    """
    Send a log through http post
    :param log_data: a string to be sent to backend instrumentation
    """

    api_endpoint = (
        os.getenv(logging.TELEMETRY_ENDPOINT_ENV_VAR_NAME) or settings.telemetry.api_url
    )
    api_key = os.getenv(logging.TELEMETRY_KEY_ENV_VAR_NAME)

    if not api_endpoint or not api_key:
        return PublishLogResult(
            result=Result.FAILURE,
            result_message=f"{logging.TELEMETRY_ENDPOINT_ENV_VAR_NAME} or {logging.TELEMETRY_KEY_ENV_VAR_NAME} not found in environment variables",
        )

    try:
        result = requests.post(
            url=api_endpoint, headers={"Api-Key": api_key}, data=log_data
        )
    except Exception as e:
        return PublishLogResult(
            result=Result.FAILURE,
            result_message=f'Error posting log to {api_endpoint}: "{e}"',
        )

    return PublishLogResult(result=Result.SUCCESS, result_message=result.text)


def secureli_version() -> str:
    """Leverage package resources to determine the current version of secureli"""
    return version("secureli")


def merge_scan_results(results: list[ScanResult]):
    """
    Creates a single ScanResult from multiple ScanResults
    :param results: The list of ScanResults to merge
    :return A single ScanResult
    """
    final_successful = True
    final_output = ""
    final_failures: list[ScanFailure] = []

    for result in results:
        if result:
            final_successful = final_successful and result.successful
            final_output = final_output + (result.output or "") + "\n"
            final_failures = final_failures + result.failures

    return ScanResult(
        successful=final_successful, output=final_output, failures=final_failures
    )


def generate_unique_id() -> str:
    """
    A unique identifier representing the log entry, including various
    bits specific to the user and environment
    """
    origin_email_branch = f"{origin_url()}|{git_user_email()}|{current_branch_name()}"
    return f"{uuid4()}|{origin_email_branch}"

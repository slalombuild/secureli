import requests
import os
from secureli.consts.logging import (
    TELEMETRY_ENDPOINT_ENV_VAR_NAME,
    TELEMETRY_KEY_ENV_VAR_NAME,
)
from secureli.models.publish_results import PublishLogResult
from secureli.models.result import Result

from secureli.services.scanner import Failure
from collections import Counter

from secureli.settings import Settings


def convert_failures_to_failure_count(failure_list: list[Failure]):
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


def post_log(log_data: str, settings: Settings) -> PublishLogResult:
    """
    Send a log through http post
    :param log_data: a string to be sent to backend instrumentation
    """

    api_endpoint = (
        os.getenv(TELEMETRY_ENDPOINT_ENV_VAR_NAME) or settings.telemetry.api_url
    )
    api_key = os.getenv(TELEMETRY_KEY_ENV_VAR_NAME)

    if not api_endpoint or not api_key:
        return PublishLogResult(
            result=Result.FAILURE,
            result_message=f"{TELEMETRY_ENDPOINT_ENV_VAR_NAME} or {TELEMETRY_KEY_ENV_VAR_NAME} not found in environment variables",
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

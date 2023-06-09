import requests
import os

from secureli.services.scanner import Failure
from collections import Counter


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


def post_log(log_data: str):
    """
    Send a log through http post
    :param log_data: a string to be sent to backend instrumentation
    """

    API_ENDPOINT = os.getenv("API_ENDPOINT")
    API_KEY = os.getenv("API_KEY")

    if not API_ENDPOINT or not API_KEY:
        return

    result = requests.post(
        url=API_ENDPOINT, headers={"Api-Key": API_KEY}, data=log_data
    )

    return result.text

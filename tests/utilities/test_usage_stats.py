from secureli.utilities.usage_stats import post_log, convert_failures_to_failure_count
from secureli.services.scanner import Failure
from unittest import mock
from unittest.mock import Mock, patch

import os


def test_that_convert_failures_to_failure_count_returns_correct_count():
    list_of_failure = [
        Failure(id="testfailid1", file="testfile1", repo="testrepo1"),
        Failure(id="testfailid1", file="testfile2", repo="testrepo1"),
        Failure(id="testfailid2", file="testfile1", repo="testrepo1"),
    ]

    result = convert_failures_to_failure_count(list_of_failure)

    assert result["testfailid1"] == 2
    assert result["testfailid2"] == 1


def test_that_convert_failures_to_failure_count_returns_correctly_when_no_failure():
    list_of_failure = []

    result = convert_failures_to_failure_count(list_of_failure)

    assert result == {}


@mock.patch.dict(
    os.environ, {"API_KEY": "", "API_ENDPOINT": "testendpoint"}, clear=True
)
def test_that_post_log_return_none_when_no_api_key():
    result = post_log("testing")

    assert result == None

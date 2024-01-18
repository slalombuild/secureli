from secureli.models.publish_results import PublishLogResult
from secureli.models.result import Result
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
def test_post_log_with_no_api_key():
    result = post_log("testing")

    assert result == PublishLogResult(
        result=Result.FAILURE,
        result_message="API_ENDPOINT or API_KEY not found in environment variables",
    )


# pragma: allowlist nextline secret
@mock.patch.dict(os.environ, {"API_KEY": "testkey", "API_ENDPOINT": ""}, clear=True)
def test_post_log_with_no_api_endpoint():
    result = post_log("testing")

    assert result == PublishLogResult(
        result=Result.FAILURE,
        result_message="API_ENDPOINT or API_KEY not found in environment variables",
    )


@mock.patch.dict(
    os.environ,
    {"API_KEY": "testkey", "API_ENDPOINT": "testendpoint"},  # pragma: allowlist secret
    clear=True,
)
@patch("requests.post")
def test_post_log_http_error(mock_requests):
    mock_requests.side_effect = Exception("test exception")

    result = post_log("test_log_data")

    mock_requests.assert_called_once()
    assert result == PublishLogResult(
        result=Result.FAILURE,
        result_message='Error posting log to testendpoint: "test exception"',
    )


@mock.patch.dict(
    os.environ,
    {"API_KEY": "testkey", "API_ENDPOINT": "testendpoint"},  # pragma: allowlist secret
    clear=True,
)
@patch("requests.post")
def test_post_log_happy_path(mock_requests):
    mock_requests.return_value = Mock(status_code=202, text="sample-response")

    result = post_log("test_log_data")

    mock_requests.assert_called_once()
    assert result == PublishLogResult(
        result=Result.SUCCESS, result_message="sample-response"
    )

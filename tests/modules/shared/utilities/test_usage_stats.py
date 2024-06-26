from secureli.modules.observability.consts import logging
from secureli.modules.shared.models.publish_results import PublishLogResult
from secureli.modules.shared.models.repository import TelemetrySettings
from secureli.modules.shared.models.result import Result
from secureli.modules.shared.models.scan import ScanFailure
from secureli.settings import Settings
from secureli.modules.shared import utilities
from unittest import mock
from unittest.mock import Mock, patch

import os


def test_that_convert_failures_to_failure_count_returns_correct_count():
    list_of_failure = [
        ScanFailure(
            id="testfailid1",
            file="testfile1",
            repo="testrepo1",
            exitCode="SCAN_ISSUES_DETECTED",
        ),
        ScanFailure(
            id="testfailid1",
            file="testfile2",
            repo="testrepo1",
            exitCode="PII_SCAN_ISSUES_DETECTED",
        ),
        ScanFailure(
            id="testfailid2",
            file="testfile1",
            repo="testrepo1",
            exitCode="VALIDATION_ERROR",
        ),
    ]

    result = utilities.convert_failures_to_failure_count(list_of_failure)

    assert result["testfailid1"] == 2
    assert result["testfailid2"] == 1


def test_that_convert_failures_to_failure_count_returns_correctly_when_no_failure():
    list_of_failure = []

    result = utilities.convert_failures_to_failure_count(list_of_failure)

    assert result == {}


@mock.patch.dict(
    os.environ,
    {
        f"{logging.TELEMETRY_ENDPOINT_ENV_VAR_NAME}": "testendpoint",
        f"{logging.TELEMETRY_KEY_ENV_VAR_NAME}": "",
    },
    clear=True,
)
@patch("requests.post")
def test_post_log_with_no_api_key(mock_requests):
    result = utilities.post_log("testing", Settings())

    mock_requests.assert_not_called()

    assert result == PublishLogResult(
        result=Result.FAILURE,
        result_message="SECURELI_LOGGING_API_ENDPOINT or SECURELI_LOGGING_API_KEY not found in environment variables",
    )


# pragma: allowlist nextline secret
@mock.patch.dict(
    os.environ,
    {
        f"{logging.TELEMETRY_ENDPOINT_ENV_VAR_NAME}": "",
        f"{logging.TELEMETRY_KEY_ENV_VAR_NAME}": "testkey",
    },
    clear=True,
)
@patch("requests.post")
def test_post_log_with_no_api_endpoint(mock_requests):
    result = utilities.post_log(
        "testing", Settings(telemetry=TelemetrySettings(api_url=None))
    )

    mock_requests.assert_not_called()

    assert result == PublishLogResult(
        result=Result.FAILURE,
        result_message="SECURELI_LOGGING_API_ENDPOINT or SECURELI_LOGGING_API_KEY not found in environment variables",
    )


@mock.patch.dict(
    os.environ,
    {
        f"{logging.TELEMETRY_ENDPOINT_ENV_VAR_NAME}": "testendpoint",
        f"{logging.TELEMETRY_KEY_ENV_VAR_NAME}": "testkey",
    },  # pragma: allowlist secret
    clear=True,
)
@patch("requests.post")
def test_post_log_http_error(mock_requests):
    mock_requests.side_effect = Exception("test exception")

    result = utilities.post_log("test_log_data", Settings())

    mock_requests.assert_called_once_with(
        url="testendpoint", headers={"Api-Key": "testkey"}, data="test_log_data"
    )
    assert result == PublishLogResult(
        result=Result.FAILURE,
        result_message='Error posting log to testendpoint: "test exception"',
    )


@mock.patch.dict(
    os.environ,
    {
        f"{logging.TELEMETRY_ENDPOINT_ENV_VAR_NAME}": "testendpoint",
        f"{logging.TELEMETRY_KEY_ENV_VAR_NAME}": "testkey",
    },  # pragma: allowlist secret
    clear=True,
)
@patch("requests.post")
def test_post_log_happy_path(mock_requests):
    mock_requests.return_value = Mock(status_code=202, text="sample-response")

    result = utilities.post_log("test_log_data", Settings())

    mock_requests.assert_called_once_with(
        url="testendpoint", headers={"Api-Key": "testkey"}, data="test_log_data"
    )
    assert result == PublishLogResult(
        result=Result.SUCCESS, result_message="sample-response"
    )


@mock.patch.dict(
    os.environ,
    {
        f"{logging.TELEMETRY_ENDPOINT_ENV_VAR_NAME}": "",
        f"{logging.TELEMETRY_KEY_ENV_VAR_NAME}": "testkey",
    },  # pragma: allowlist secret
    clear=True,
)
@patch("requests.post")
def test_post_log_uses_settings_endpoint_if_no_env_endpoint(mock_requests):
    mock_requests.return_value = Mock(status_code=202, text="sample-response")

    result = utilities.post_log(
        "test_log_data", Settings(telemetry=TelemetrySettings(api_url="testendpoint"))
    )

    mock_requests.assert_called_once_with(
        url="testendpoint", headers={"Api-Key": "testkey"}, data="test_log_data"
    )
    assert result == PublishLogResult(
        result=Result.SUCCESS, result_message="sample-response"
    )

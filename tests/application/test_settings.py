from unittest.mock import MagicMock

from pytest_mock import MockerFixture

from secureli import settings


def test_that_secureli_yaml_settings_guards_against_missing_yaml_file(
    mocker: MockerFixture,
):
    path_instance = MagicMock()
    path_instance.exists.return_value = False
    path_class = mocker.patch("secureli.settings.Path")
    path_class.return_value = path_instance

    assert not settings.secureli_yaml_settings(settings.Settings())


def test_that_secureli_yaml_settings_processes_present_yaml_file(
    mocker: MockerFixture,
):
    path_instance = MagicMock()
    path_instance.exists.return_value = True
    path_class = mocker.patch("secureli.settings.Path")
    path_class.return_value = path_instance
    mock_open = mocker.mock_open(
        read_data="""
        language_support:
            command_timeout_seconds: 12345
        """
    )
    mocker.patch("builtins.open", mock_open)

    result = settings.secureli_yaml_settings(settings.Settings())
    assert "language_support" in result
    assert result["language_support"]["command_timeout_seconds"] == 12345

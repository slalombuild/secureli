from secureli.utilities.logging import EchoLevel


def test_that_echo_level_str_returns_enum_val():
    level = EchoLevel.info

    assert str(level) == level.value


def test_that_echo_level_repr_returns_str_implementation():
    level = EchoLevel.debug

    assert repr(level) == str(level)

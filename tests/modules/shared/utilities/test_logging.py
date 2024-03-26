from secureli.modules.shared.models.echo import Level


def test_that_echo_level_str_returns_enum_val():
    level = Level.info

    assert str(level) == level.value


def test_that_echo_level_repr_returns_str_implementation():
    level = Level.debug

    assert repr(level) == str(level)

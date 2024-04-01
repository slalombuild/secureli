from secureli.modules.shared.utilities import combine_patterns


def test_that_combine_patterns_returns_none_for_empty_list():
    result = combine_patterns([])
    assert result is None


def test_that_combine_patterns_returns_a_single_pattern_as_the_pattern():
    result = combine_patterns(["mock_pattern1"])
    assert result == "mock_pattern1"


def test_that_combine_patterns_returns_multiple_patterns_as_a_combined_pattern():
    result = combine_patterns(["mock_pattern1", "mock_pattern2"])
    assert result == "^(mock_pattern1|mock_pattern2)$"


def test_that_combine_patterns_addresses_duplicate_capture_group_issue():
    pattern1 = "*\\.py(?:(?P<ps_d>/).*)?$"
    pattern2 = "*\\.txt(?:(?P<ps_d>/).*)?$"
    result = combine_patterns([pattern1, pattern2])
    assert result == "^(*\\.py(?:(?P<ps_d0>/).*)?$|*\\.txt(?:(?P<ps_d1>/).*)?$)$"

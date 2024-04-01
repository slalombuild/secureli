from secureli.modules.shared.utilities import format_sentence_list


def test_format_sentence_list_handles_missing_list():
    result = format_sentence_list(None)

    assert result == ""


def test_format_sentence_list_handles_empty_list():
    result = format_sentence_list([])

    assert result == ""


def test_format_sentence_list_handles_two_items():
    items = ["RadLang", "CoolLang"]

    result = format_sentence_list(items)
    assert result == "RadLang and CoolLang"


def test_format_sentence_list_handles_more_than_two_items():
    items = ["RadLang", "CoolLang", "SuperLang", "CoffeeLang"]

    result = format_sentence_list(items)
    assert result == "RadLang, CoolLang, SuperLang, and CoffeeLang"

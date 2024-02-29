import unicodedata
import re


def slugify(value: str):
    """
    Taken from https://github.com/django/django/blob/master/django/utils/text.py
    Convert to ASCII if 'allow_unicode' is False. Convert spaces or repeated
    dashes to single dashes. Remove characters that aren't alphanumerics,
    underscores, or hyphens. Convert to lowercase. Also strip leading and
    trailing whitespace, dashes, and underscores.
    """

    illegal_character_mappings = {
        "#": "Sharp",
        "%": "Percent",
        "&": "Ampersand",
        "{": "LeftCurlyBracket",
        "}": "RightCurlyBracket",
        "\\": "BackSlash",
        "<": "LeftAngleBracket",
        ">": "RightAngleBracket",
        "*": "Star",
        "?": "Question",
        "/": "ForwardSlash",
        "$": "DollarSign",
        "!": "Exclamation",
        ":": "Colon",
        "@": "At",
        "+": "Plus",
    }

    for illegal_character in illegal_character_mappings.keys():
        replacement = illegal_character_mappings[illegal_character]
        value = value.replace(illegal_character, replacement)

    value = str(value)
    value = (
        unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    )
    value = re.sub(r"[^\w\s-]", "", value.lower())
    return re.sub(r"[-\s]+", "-", value).strip("-_")

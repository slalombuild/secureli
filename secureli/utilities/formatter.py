def format_sentence_list(items: list[str]) -> str:
    """
    Formats a list of string values to a comma separated
    string for use in a sentence structure.
    :param items: list of strings to join
    :return string of joined values as a sentence comma list
    i.e. "x, y, and z" or "x and y"
    """
    if not items:
        return ""
    elif len(items) == 1:
        return items[0]
    and_separator = ", and " if len(items) > 2 else " and "
    return ", ".join(items[:-1]) + and_separator + items[-1]

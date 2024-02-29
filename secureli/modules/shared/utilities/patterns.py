from typing import Optional


def combine_patterns(patterns: list[str]) -> Optional[str]:
    """
    Combines a set of patterns from pathspec into a single combined regex
    suitable for use in circumstances that require a broad matching, such as
    re.find_all or a pre-commit exclusion pattern.

    Calling this with an empty set of patterns will return None
    :param patterns: The pattern strings provided by pathspec to combine
    :return: a combined pattern containing the one or more patterns supplied, or None
    if no patterns were supplied
    """
    if not patterns:
        return None

    if len(patterns) == 1:
        return patterns[0]

    # Don't mutate the input
    ignored_file_patterns = patterns.copy()

    # Quick sanitization process. Ultimately we combine all the regexes into a single
    # entry, and all patterns are generated with a capture group with the same ID, which
    # is invalid. We need to make sure every capture group is unique to combine them
    # into a single expression. This is not my favorite.
    for i in range(0, len(ignored_file_patterns)):
        ignored_file_patterns[i] = str.replace(
            ignored_file_patterns[i], "ps_d", f"ps_d{i}"
        )
    combined_patterns = str.join("|", ignored_file_patterns)
    combined_ignore_pattern = f"^({combined_patterns})$"
    return combined_ignore_pattern

import re


def round_floats_in_text(content: str, digits: int) -> str:
    """
    Rounds all floats in the given string to the specified number of significant digits.
    Avoids altering IP-like sequences, timestamps, and URLs.
    """

    # Detect IPv4 addresses
    ip_pattern = re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b")

    # Detect ISO8601-like timestamps (with optional Z or offset)
    timestamp_pattern = re.compile(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?"
    )

    # Detect URLs (http or https)
    url_pattern = re.compile(r"https?://[^\s]+", re.IGNORECASE)

    placeholders = []

    def placeholder_replacer(match) -> str:
        placeholders.append(match.group(0))
        return f"__PLACEHOLDER_{len(placeholders) - 1}__"

    # Temporarily replace IPs, timestamps, and URLs with placeholders
    content_safe = ip_pattern.sub(placeholder_replacer, content)
    content_safe = timestamp_pattern.sub(placeholder_replacer, content_safe)
    content_safe = url_pattern.sub(placeholder_replacer, content_safe)

    # Regex: match numbers (floats or scientific notation)
    number_pattern = re.compile(
        r"""
        (?<![\w.])            # not preceded by word char or dot
        (                      # start group for number
            (?:\d*\.\d+|\d+\.\d*|\d+)  # decimals or integers
            (?:[eE][+-]?\d+)?  # optional exponent
        )
        (?![\w.])             # not followed by word char or dot
    """,
        re.VERBOSE,
    )

    def replacer(match) -> str:
        num_str = match.group(0)
        try:
            num = float(num_str)
            return f"{num:.{digits}g}"
        except ValueError:
            return num_str

    rounded = number_pattern.sub(replacer, content_safe)

    # Restore placeholders
    for i, original in enumerate(placeholders):
        rounded = rounded.replace(f"__PLACEHOLDER_{i}__", original)

    return rounded

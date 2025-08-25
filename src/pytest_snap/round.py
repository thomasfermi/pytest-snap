import re


def round_floats_in_text(content: str, digits: int) -> str:
    """
    Round floating point numbers in text to specified significant digits.
    Avoids rounding numbers that are part of:
    - IP addresses
    - Semantic versions
    - Timestamps/dates
    - URLs
    - Plain integers
    Note that this is a simple heuristic which will work well for many cases, but certainly not for all.
    Written by Claude Sonnet 4.0.
    """
    combined_pattern = r"""
        (?P<ip>\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b)|
        (?P<semver>\b\d+\.\d+\.\d+\b)|
        (?P<iso_timestamp>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?)|
        (?P<date>\d{4}-\d{2}-\d{2})|
        (?P<time>\d{2}:\d{2}:\d{2}(?:\.\d+)?)|
        (?P<url>https?://[^\s]+)|
        (?P<float>-?\d+\.?\d*(?:[eE][+-]?\d+)?)
    """

    pattern = re.compile(combined_pattern, re.VERBOSE)

    result_parts = []
    last_end = 0

    for match in pattern.finditer(content):
        # Add text before this match
        result_parts.append(content[last_end : match.start()])
        if match.lastgroup == "float":
            number_text = match.group("float")

            # Skip if it's actually a plain integer
            if "." not in number_text and "e" not in number_text.lower():
                result_parts.append(number_text)
            else:
                # Try to round it
                try:
                    number = float(number_text)
                    rounded = f"{number:.{digits}g}"
                    result_parts.append(rounded)
                except ValueError:
                    result_parts.append(number_text)
        else:
            # This is an exclusion pattern - keep as-is
            result_parts.append(match.group(0))

        last_end = match.end()

    # Add remaining text
    result_parts.append(content[last_end:])

    return "".join(result_parts)

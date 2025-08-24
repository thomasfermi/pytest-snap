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

    # Pattern to match floating point numbers (including scientific notation)
    # This matches:
    # - Optional minus sign
    # - One or more digits
    # - Optional decimal point followed by digits
    # - Optional scientific notation (e/E followed by optional +/- and digits)
    float_pattern = r"-?\d+\.?\d*(?:[eE][+-]?\d+)?"

    def should_skip_rounding(match, full_text, start_pos, end_pos):
        """Check if this number should be skipped from rounding."""

        # Check if it's actually a plain integer (no decimal point or scientific notation)
        number_text = match.group(0)
        if "." not in number_text and "e" not in number_text.lower():
            return True

        # Find all IP addresses and check if our match overlaps
        ip_pattern = r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"
        for ip_match in re.finditer(ip_pattern, full_text):
            # Check if our number is part of this IP address
            if start_pos >= ip_match.start() and end_pos <= ip_match.end():
                return True

        # Find all semantic versions and check if our match overlaps
        semver_pattern = r"\b\d+\.\d+\.\d+\b"
        for semver_match in re.finditer(semver_pattern, full_text):
            # Check if our number is part of this semver
            if start_pos >= semver_match.start() and end_pos <= semver_match.end():
                return True

        # Find all timestamps/dates and check if our match overlaps
        timestamp_patterns = [
            r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+-]\d{2}:\d{2})?",  # ISO timestamp
            r"\d{4}-\d{2}-\d{2}",  # Date
            r"\d{2}:\d{2}:\d{2}(?:\.\d+)?",  # Time
        ]
        for pattern in timestamp_patterns:
            for ts_match in re.finditer(pattern, full_text):
                # Check if our number is part of this timestamp
                if start_pos >= ts_match.start() and end_pos <= ts_match.end():
                    return True

        # Find all URLs and check if our match overlaps
        url_pattern = r"https?://[^\s]+"
        for url_match in re.finditer(url_pattern, full_text):
            # Check if our number is part of this URL
            if start_pos >= url_match.start() and end_pos <= url_match.end():
                return True

        return False

    def replace_float(match):
        """Replace a float with its rounded version."""
        start_pos = match.start()
        end_pos = match.end()

        # Check if we should skip this number
        if should_skip_rounding(match, content, start_pos, end_pos):
            return match.group(0)

        # Parse and round the number
        try:
            number = float(match.group(0))
            # Use 'g' format for significant digits
            rounded = f"{number:.{digits}g}"
            return rounded
        except ValueError:
            # If we can't parse it, return as-is
            return match.group(0)

    # Apply the replacement
    result = re.sub(float_pattern, replace_float, content)
    return result

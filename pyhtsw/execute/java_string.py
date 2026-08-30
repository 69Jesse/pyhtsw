__all__ = (
    'java_string_length',
    'exceeds_java_length',
)


def java_string_length(value: str) -> int:
    """Length of `value` in UTF-16 code units, the unit Java's `String.length()`
    and htsw's own `.length` checks both count in. A code point above U+FFFF
    counts as 2."""
    return len(value) + sum(1 for char in value if ord(char) > 0xFFFF)


def exceeds_java_length(value: str, limit: int) -> int | None:
    """The measured length when `value` is over `limit`, else None. Surrounding
    double quotes are stripped first, matching htsw's `parseValue`."""
    if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
        value = value[1:-1]
    length = java_string_length(value)
    return length if length > limit else None

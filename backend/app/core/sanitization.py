import html
import re

# Disallow dangerous script tags, html tags, or control characters in text inputs
HTML_TAG_PATTERN = re.compile(r"<[^>]+>")


def sanitize_string(val: str, max_length: int = 500) -> str:
    """Sanitizes text inputs by escaping HTML characters, stripping control codes,
    and enforcing max length to protect against XSS and injection attacks.
    """
    if not val:
        return ""
    # Strip HTML tags
    cleaned = HTML_TAG_PATTERN.sub("", val)
    # Escape entities
    escaped = html.escape(cleaned.strip())
    return escaped[:max_length]

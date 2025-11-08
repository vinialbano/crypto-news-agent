"""URL normalization utilities for duplicate detection."""

from urllib.parse import urlparse, urlunparse


def normalize_url(url: str) -> str:
    """
    Normalize a URL for duplicate detection by removing query parameters,
    fragments, and standardizing the format.

    This helps prevent duplicate articles with the same content but different
    tracking parameters (utm_*, fbclid, etc.) from being stored multiple times.

    Args:
        url: The URL to normalize

    Returns:
        Normalized URL without query params, fragments, or trailing slashes

    Examples:
        >>> normalize_url("https://example.com/article?utm_source=rss#comment")
        'https://example.com/article'

        >>> normalize_url("HTTP://Example.com/Article/?foo=bar")
        'https://example.com/article'

        >>> normalize_url("https://example.com/article/")
        'https://example.com/article'
    """
    if not url or not url.strip():
        return ""

    url = url.strip()

    # Parse the URL
    parsed = urlparse(url)

    # Normalize scheme (force https if http, preserve others like ftp)
    scheme = parsed.scheme.lower()
    if scheme == "http":
        scheme = "https"

    # Normalize domain (lowercase)
    netloc = parsed.netloc.lower()

    # Get path without trailing slash (unless it's the root path)
    # Also lowercase the path for normalization
    path = parsed.path.lower().rstrip("/") if parsed.path != "/" else "/"

    # Reconstruct URL without query params and fragments
    # Format: (scheme, netloc, path, params, query, fragment)
    # We keep params empty, query empty, fragment empty
    normalized = urlunparse((scheme, netloc, path, "", "", ""))

    return normalized

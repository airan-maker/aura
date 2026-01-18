"""URL validation utilities."""

from urllib.parse import urlparse


def validate_url(url: str) -> bool:
    """
    Validate URL format and prevent SSRF attacks.

    Args:
        url: URL string to validate

    Returns:
        True if URL is valid and safe, False otherwise
    """
    try:
        result = urlparse(url)

        # Check protocol
        if result.scheme not in ['http', 'https']:
            return False

        # Check domain exists
        if not result.netloc:
            return False

        # Prevent SSRF - block internal IPs
        netloc_lower = result.netloc.lower()

        # Block localhost and loopback
        if any(x in netloc_lower for x in ['localhost', '127.', '::1']):
            return False

        # Block private IP ranges
        if any(netloc_lower.startswith(prefix) for prefix in ['192.168.', '10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.', '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.', '172.27.', '172.28.', '172.29.', '172.30.', '172.31.']):
            return False

        return True

    except Exception:
        return False

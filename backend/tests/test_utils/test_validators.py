"""Tests for URL validation utilities."""

import pytest
from app.utils.validators import validate_url


def test_validate_url_valid_http():
    """Test validation of valid HTTP URLs."""
    assert validate_url("http://example.com") is True
    assert validate_url("http://www.example.com") is True
    assert validate_url("http://example.com/path") is True
    assert validate_url("http://example.com:8080") is True


def test_validate_url_valid_https():
    """Test validation of valid HTTPS URLs."""
    assert validate_url("https://example.com") is True
    assert validate_url("https://www.example.com") is True
    assert validate_url("https://example.com/path/to/page") is True
    assert validate_url("https://sub.example.com") is True


def test_validate_url_invalid_protocol():
    """Test rejection of invalid protocols."""
    assert validate_url("ftp://example.com") is False
    assert validate_url("file:///path/to/file") is False
    assert validate_url("javascript:alert(1)") is False


def test_validate_url_ssrf_protection_localhost():
    """Test SSRF protection - block localhost."""
    assert validate_url("http://localhost") is False
    assert validate_url("http://localhost:8080") is False
    assert validate_url("http://127.0.0.1") is False
    assert validate_url("http://127.0.0.1:3000") is False


def test_validate_url_ssrf_protection_private_ips():
    """Test SSRF protection - block private IP ranges."""
    # 192.168.x.x
    assert validate_url("http://192.168.1.1") is False
    assert validate_url("http://192.168.0.100") is False

    # 10.x.x.x
    assert validate_url("http://10.0.0.1") is False
    assert validate_url("http://10.255.255.255") is False

    # 172.16.x.x - 172.31.x.x
    assert validate_url("http://172.16.0.1") is False
    assert validate_url("http://172.31.255.255") is False


def test_validate_url_no_domain():
    """Test rejection of URLs without domain."""
    assert validate_url("http://") is False
    assert validate_url("https://") is False


def test_validate_url_malformed():
    """Test rejection of malformed URLs."""
    assert validate_url("not a url") is False
    assert validate_url("") is False
    assert validate_url("example.com") is False  # No protocol


def test_validate_url_with_query_params():
    """Test validation of URLs with query parameters."""
    assert validate_url("https://example.com?foo=bar") is True
    assert validate_url("https://example.com?foo=bar&baz=qux") is True


def test_validate_url_with_fragment():
    """Test validation of URLs with fragments."""
    assert validate_url("https://example.com#section") is True
    assert validate_url("https://example.com/page#top") is True


def test_validate_url_internationalized():
    """Test validation of internationalized domain names."""
    # Should work with IDN domains
    assert validate_url("https://münchen.de") is True or validate_url("https://xn--mnchen-3ya.de") is True

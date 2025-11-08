"""Tests for URL normalization utilities."""

import pytest

from app.services.url_utils import normalize_url


class TestNormalizeUrl:
    """Test cases for URL normalization function."""

    def test_removes_query_parameters(self):
        """Test that query parameters are removed."""
        url = "https://example.com/article?utm_source=rss&utm_medium=feed"
        expected = "https://example.com/article"
        assert normalize_url(url) == expected

    def test_removes_fragments(self):
        """Test that URL fragments are removed."""
        url = "https://example.com/article#comment-section"
        expected = "https://example.com/article"
        assert normalize_url(url) == expected

    def test_removes_both_query_and_fragment(self):
        """Test that both query params and fragments are removed."""
        url = "https://example.com/article?utm_source=twitter#comments"
        expected = "https://example.com/article"
        assert normalize_url(url) == expected

    def test_normalizes_scheme_http_to_https(self):
        """Test that http:// is converted to https://."""
        url = "http://example.com/article"
        expected = "https://example.com/article"
        assert normalize_url(url) == expected

    def test_preserves_https_scheme(self):
        """Test that https:// scheme is preserved."""
        url = "https://example.com/article"
        expected = "https://example.com/article"
        assert normalize_url(url) == expected

    def test_lowercases_domain(self):
        """Test that domain is converted to lowercase."""
        url = "https://EXAMPLE.COM/Article"
        expected = "https://example.com/article"
        assert normalize_url(url) == expected

    def test_removes_trailing_slash(self):
        """Test that trailing slash is removed from path."""
        url = "https://example.com/article/"
        expected = "https://example.com/article"
        assert normalize_url(url) == expected

    def test_preserves_root_path_slash(self):
        """Test that root path slash is preserved."""
        url = "https://example.com/"
        expected = "https://example.com/"
        assert normalize_url(url) == expected

    def test_handles_complex_cointelegraph_urls(self):
        """Test with real-world Cointelegraph URLs with tracking params."""
        urls = [
            "https://cointelegraph.com/news/bitcoin-coinbase-premium-hits-7-month-low-but-traders-spot-a-silver-lining?utm_source=rss_feed&utm_medium=rss%3Fvfff%3D1762550938%26_%3D1762550938925&utm_campaign=rss_partner_inbound",
            "https://cointelegraph.com/news/bitcoin-coinbase-premium-hits-7-month-low-but-traders-spot-a-silver-lining?utm_source=rss_feed&utm_medium=rss%3Fcb%3Dmqlmov%26timestamp%3D1762555782430%26vfff%3D1762555782&utm_campaign=rss_partner_inbound",
            "https://cointelegraph.com/news/bitcoin-coinbase-premium-hits-7-month-low-but-traders-spot-a-silver-lining?utm_source=rss_feed&utm_medium=rss%3FnoCache%3Dtrue%26r%3D1khg07&utm_campaign=rss_partner_inbound",
        ]

        expected = "https://cointelegraph.com/news/bitcoin-coinbase-premium-hits-7-month-low-but-traders-spot-a-silver-lining"

        # All variations should normalize to the same URL
        for url in urls:
            assert normalize_url(url) == expected

    def test_handles_empty_string(self):
        """Test that empty string returns empty string."""
        assert normalize_url("") == ""

    def test_handles_whitespace_only(self):
        """Test that whitespace-only string returns empty string."""
        assert normalize_url("   ") == ""

    def test_strips_leading_trailing_whitespace(self):
        """Test that leading/trailing whitespace is removed."""
        url = "  https://example.com/article  "
        expected = "https://example.com/article"
        assert normalize_url(url) == expected

    def test_preserves_path_structure(self):
        """Test that complex path structures are preserved."""
        url = "https://example.com/news/2024/11/article-title?tracking=xyz"
        expected = "https://example.com/news/2024/11/article-title"
        assert normalize_url(url) == expected

    def test_handles_subdomain(self):
        """Test that subdomains are normalized correctly."""
        url = "https://blog.Example.COM/post?id=123"
        expected = "https://blog.example.com/post"
        assert normalize_url(url) == expected

    def test_handles_port_numbers(self):
        """Test that port numbers are preserved."""
        url = "https://example.com:8080/article?query=test"
        expected = "https://example.com:8080/article"
        assert normalize_url(url) == expected

    def test_different_tracking_params_same_article(self):
        """Test that different tracking params result in same normalized URL."""
        base_url = "https://example.com/article"

        variants = [
            f"{base_url}?utm_source=rss",
            f"{base_url}?utm_source=twitter&utm_campaign=social",
            f"{base_url}?fbclid=xyz123",
            f"{base_url}?gclid=abc456&utm_medium=cpc",
        ]

        expected = base_url

        # All variants should normalize to the same URL
        normalized_urls = [normalize_url(url) for url in variants]
        assert all(normalized == expected for normalized in normalized_urls)
        # Verify all are identical
        assert len(set(normalized_urls)) == 1

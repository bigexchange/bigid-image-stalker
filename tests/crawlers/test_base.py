"""Tests for container_crawler.crawlers.base.BaseCrawler.

These tests verify the shared crawler infrastructure — HTTP helpers, owner
exclusion, filter matching, deduplication, and error handling — using a
lightweight stub that yields controlled results.
"""

from typing import Iterator

import responses

from container_crawler.crawlers.base import BaseCrawler
from container_crawler.models import ImageResult


# ---------------------------------------------------------------------------
# Stub crawler for testing base class behaviour
# ---------------------------------------------------------------------------


class StubCrawler(BaseCrawler):
    """Concrete subclass that yields pre-configured results."""

    registry_name = "stub"

    def __init__(self, config, *, results=None, raises=None):
        super().__init__(config)
        self._results = results or []
        self._raises = raises

    def search(self, term: str) -> Iterator[ImageResult]:
        if self._raises:
            raise self._raises
        yield from self._results


# ---------------------------------------------------------------------------
# HTTP helper tests
# ---------------------------------------------------------------------------


class TestHTTPHelpers:
    @responses.activate
    def test_get_success(self, sample_config):
        responses.add(
            responses.GET, "https://example.com/api", json={"ok": True}, status=200
        )
        crawler = StubCrawler(sample_config)
        resp = crawler._get("https://example.com/api")
        assert resp is not None
        assert resp.json() == {"ok": True}

    @responses.activate
    def test_get_failure_returns_none(self, sample_config):
        responses.add(responses.GET, "https://example.com/api", status=500)
        crawler = StubCrawler(sample_config)
        resp = crawler._get("https://example.com/api")
        assert resp is None

    @responses.activate
    def test_post_success(self, sample_config):
        responses.add(
            responses.POST, "https://example.com/api", json={"ok": True}, status=200
        )
        crawler = StubCrawler(sample_config)
        resp = crawler._post("https://example.com/api", json={"q": "test"})
        assert resp is not None
        assert resp.json() == {"ok": True}

    @responses.activate
    def test_post_failure_returns_none(self, sample_config):
        responses.add(responses.POST, "https://example.com/api", status=500)
        crawler = StubCrawler(sample_config)
        resp = crawler._post("https://example.com/api")
        assert resp is None


# ---------------------------------------------------------------------------
# Owner exclusion
# ---------------------------------------------------------------------------


class TestIsExcluded:
    def test_match(self, sample_config):
        crawler = StubCrawler(sample_config)
        assert crawler._is_excluded("excluded-org") is True

    def test_case_insensitive(self, sample_config):
        crawler = StubCrawler(sample_config)
        assert crawler._is_excluded("EXCLUDED-ORG") is True

    def test_no_match(self, sample_config):
        crawler = StubCrawler(sample_config)
        assert crawler._is_excluded("other-org") is False


# ---------------------------------------------------------------------------
# Filter matching
# ---------------------------------------------------------------------------


class TestMatchesFilter:
    def test_no_pattern_always_matches(self, sample_config, sample_image):
        crawler = StubCrawler(sample_config)
        assert crawler._matches_filter(sample_image) is True

    def test_matching_pattern(self, sample_config, sample_image):
        sample_config.filter_pattern = "scanner"
        crawler = StubCrawler(sample_config)
        assert crawler._matches_filter(sample_image) is True

    def test_non_matching_pattern(self, sample_config, sample_image):
        sample_config.filter_pattern = "^zzz$"
        crawler = StubCrawler(sample_config)
        assert crawler._matches_filter(sample_image) is False

    def test_case_insensitive(self, sample_config, sample_image):
        sample_config.filter_pattern = "SCANNER"
        crawler = StubCrawler(sample_config)
        assert crawler._matches_filter(sample_image) is True


# ---------------------------------------------------------------------------
# crawl() orchestration
# ---------------------------------------------------------------------------


class TestCrawl:
    def test_dedup(self, sample_config, sample_image):
        """Duplicate images (same registry:owner/name) should be collapsed to one."""
        crawler = StubCrawler(sample_config, results=[sample_image, sample_image])
        assert len(crawler.crawl()) == 1

    def test_filter_applied(self, sample_config, sample_image):
        sample_config.filter_pattern = "^zzz$"
        crawler = StubCrawler(sample_config, results=[sample_image])
        assert len(crawler.crawl()) == 0

    def test_exception_in_search_caught(self, sample_config):
        """An unexpected error in search() should not crash crawl()."""
        crawler = StubCrawler(sample_config, raises=RuntimeError("boom"))
        results = crawler.crawl()
        assert results == []

    def test_multiple_terms(self, sample_config):
        sample_config.search_terms = ["term1", "term2"]
        img1 = ImageResult(
            repo_owner="a", image_name="x", registry="stub", link="https://x"
        )
        img2 = ImageResult(
            repo_owner="b", image_name="y", registry="stub", link="https://y"
        )

        class MultiStub(BaseCrawler):
            registry_name = "stub"
            call_count = 0

            def search(self, term):
                MultiStub.call_count += 1
                if MultiStub.call_count == 1:
                    yield img1
                else:
                    yield img2

        crawler = MultiStub(sample_config)
        results = crawler.crawl()
        assert len(results) == 2

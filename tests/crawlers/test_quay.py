"""Tests for container_crawler.crawlers.quay.QuayCrawler.

Quay.io requires two HTTP endpoints per image — the search endpoint and the
per-repo stats endpoint. Both are mocked with the ``responses`` library.
"""

import re

import responses

from container_crawler.crawlers.quay import QuayCrawler, SEARCH_URL


def _search_response(results, has_additional=False):
    return {"results": results, "has_additional": has_additional}


def _repo(name, namespace):
    return {"name": name, "namespace": {"name": namespace}}


def _stats_response(counts):
    """Build a stats response with a list of count values."""
    return {"stats": [{"count": c} for c in counts]}


class TestQuaySearch:
    @responses.activate
    def test_single_page(self, sample_config):
        responses.add(
            responses.GET,
            SEARCH_URL,
            json=_search_response([_repo("scanner", "acme")]),
            status=200,
        )
        responses.add(
            responses.GET,
            re.compile(r"https://quay\.io/api/v1/repository/acme/scanner"),
            json=_stats_response([100, 200]),
            status=200,
        )
        crawler = QuayCrawler(sample_config)
        results = list(crawler.search("bigid"))
        assert len(results) == 1
        assert results[0].total_downloads == 300
        assert results[0].link == "https://quay.io/repository/acme/scanner"

    @responses.activate
    def test_pagination(self, sample_config):
        responses.add(
            responses.GET,
            SEARCH_URL,
            json=_search_response([_repo("img1", "acme")], has_additional=True),
            status=200,
        )
        responses.add(
            responses.GET,
            re.compile(r"https://quay\.io/api/v1/repository/acme/img1"),
            json=_stats_response([10]),
            status=200,
        )
        responses.add(
            responses.GET,
            SEARCH_URL,
            json=_search_response([_repo("img2", "acme")]),
            status=200,
        )
        responses.add(
            responses.GET,
            re.compile(r"https://quay\.io/api/v1/repository/acme/img2"),
            json=_stats_response([20]),
            status=200,
        )
        crawler = QuayCrawler(sample_config)
        results = list(crawler.search("bigid"))
        assert len(results) == 2

    @responses.activate
    def test_excludes_owner(self, sample_config):
        responses.add(
            responses.GET,
            SEARCH_URL,
            json=_search_response([_repo("scanner", "excluded-org")]),
            status=200,
        )
        crawler = QuayCrawler(sample_config)
        assert list(crawler.search("bigid")) == []

    @responses.activate
    def test_skips_empty_name(self, sample_config):
        responses.add(
            responses.GET,
            SEARCH_URL,
            json=_search_response([_repo("", "acme")]),
            status=200,
        )
        crawler = QuayCrawler(sample_config)
        assert list(crawler.search("bigid")) == []

    @responses.activate
    def test_skips_empty_namespace(self, sample_config):
        responses.add(
            responses.GET,
            SEARCH_URL,
            json=_search_response([{"name": "scanner", "namespace": {"name": ""}}]),
            status=200,
        )
        crawler = QuayCrawler(sample_config)
        assert list(crawler.search("bigid")) == []

    @responses.activate
    def test_skips_when_stats_unavailable(self, sample_config):
        """If the per-repo stats endpoint fails, the image should be skipped."""
        responses.add(
            responses.GET,
            SEARCH_URL,
            json=_search_response([_repo("scanner", "acme")]),
            status=200,
        )
        responses.add(
            responses.GET,
            re.compile(r"https://quay\.io/api/v1/repository/acme/scanner"),
            status=500,
        )
        crawler = QuayCrawler(sample_config)
        assert list(crawler.search("bigid")) == []

    @responses.activate
    def test_empty_results(self, sample_config):
        responses.add(
            responses.GET,
            SEARCH_URL,
            json=_search_response([]),
            status=200,
        )
        crawler = QuayCrawler(sample_config)
        assert list(crawler.search("bigid")) == []

    @responses.activate
    def test_search_request_failure(self, sample_config):
        responses.add(responses.GET, SEARCH_URL, status=500)
        crawler = QuayCrawler(sample_config)
        assert list(crawler.search("bigid")) == []

    @responses.activate
    def test_get_total_downloads_sums(self, sample_config):
        responses.add(
            responses.GET,
            re.compile(r"https://quay\.io/api/v1/repository/acme/scanner"),
            json=_stats_response([10, 20, 30]),
            status=200,
        )
        crawler = QuayCrawler(sample_config)
        assert crawler._get_total_downloads("acme", "scanner") == 60

"""Tests for container_crawler.crawlers.ecr.ECRCrawler.

All HTTP calls are mocked with the ``responses`` library — no real network
traffic is generated.
"""

import json

import responses

from container_crawler.crawlers.ecr import ECRCrawler, SEARCH_URL


def _ecr_response(repos, next_token=None, total_results=None):
    """Build a mock ECR search response body."""
    if total_results is None:
        total_results = len(repos)
    body = {
        "totalResults": total_results,
        "repositoryCatalogSearchResultList": repos,
    }
    if next_token:
        body["nextToken"] = next_token
    return body


def _repo(name, owner, downloads=0):
    return {
        "repositoryName": name,
        "primaryRegistryAliasName": owner,
        "downloadCount": downloads,
    }


class TestECRSearch:

    @responses.activate
    def test_single_page(self, sample_config):
        responses.add(
            responses.POST, SEARCH_URL,
            json=_ecr_response([_repo("img1", "acme", 10), _repo("img2", "acme", 20)]),
            status=200,
        )
        crawler = ECRCrawler(sample_config)
        results = list(crawler.search("bigid"))
        assert len(results) == 2
        assert results[0].image_name == "img1"
        assert results[1].total_downloads == 20

    @responses.activate
    def test_pagination(self, sample_config):
        responses.add(
            responses.POST, SEARCH_URL,
            json=_ecr_response([_repo("img1", "acme")], next_token="tok1"),
            status=200,
        )
        responses.add(
            responses.POST, SEARCH_URL,
            json=_ecr_response([_repo("img2", "acme")]),
            status=200,
        )
        crawler = ECRCrawler(sample_config)
        results = list(crawler.search("bigid"))
        assert len(results) == 2

    @responses.activate
    def test_excludes_owner(self, sample_config):
        responses.add(
            responses.POST, SEARCH_URL,
            json=_ecr_response([_repo("img1", "excluded-org")]),
            status=200,
        )
        crawler = ECRCrawler(sample_config)
        results = list(crawler.search("bigid"))
        assert len(results) == 0

    @responses.activate
    def test_skips_empty_name(self, sample_config):
        responses.add(
            responses.POST, SEARCH_URL,
            json=_ecr_response([_repo("", "acme")]),
            status=200,
        )
        crawler = ECRCrawler(sample_config)
        assert list(crawler.search("bigid")) == []

    @responses.activate
    def test_skips_empty_owner(self, sample_config):
        responses.add(
            responses.POST, SEARCH_URL,
            json=_ecr_response([_repo("img1", "")]),
            status=200,
        )
        crawler = ECRCrawler(sample_config)
        assert list(crawler.search("bigid")) == []

    @responses.activate
    def test_zero_results(self, sample_config):
        responses.add(
            responses.POST, SEARCH_URL,
            json=_ecr_response([], total_results=0),
            status=200,
        )
        crawler = ECRCrawler(sample_config)
        assert list(crawler.search("bigid")) == []

    @responses.activate
    def test_request_failure(self, sample_config):
        responses.add(responses.POST, SEARCH_URL, status=500)
        crawler = ECRCrawler(sample_config)
        assert list(crawler.search("bigid")) == []

    @responses.activate
    def test_link_format(self, sample_config):
        responses.add(
            responses.POST, SEARCH_URL,
            json=_ecr_response([_repo("myimage", "myowner")]),
            status=200,
        )
        crawler = ECRCrawler(sample_config)
        results = list(crawler.search("bigid"))
        assert results[0].link == "https://gallery.ecr.aws/myowner/myimage"

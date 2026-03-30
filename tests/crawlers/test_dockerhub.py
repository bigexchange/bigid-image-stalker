"""Tests for container_crawler.crawlers.dockerhub.DockerHubCrawler.

All HTTP calls are mocked with the ``responses`` library.
"""

import responses

from container_crawler.crawlers.dockerhub import DockerHubCrawler, SEARCH_URL


def _dh_response(summaries, count=None, next_url=None):
    """Build a mock Docker Hub search response body."""
    if count is None:
        count = len(summaries)
    body = {"count": count, "summaries": summaries, "next": next_url}
    return body


def _summary(name, publisher, downloads=0):
    return {
        "name": name,
        "publisher": {"name": publisher},
        "pull_count": downloads,
    }


class TestDockerHubSearch:
    @responses.activate
    def test_single_page(self, sample_config):
        responses.add(
            responses.GET,
            SEARCH_URL,
            json=_dh_response(
                [_summary("app", "acme", 100), _summary("web", "acme", 200)]
            ),
            status=200,
        )
        crawler = DockerHubCrawler(sample_config)
        results = list(crawler.search("bigid"))
        assert len(results) == 2
        assert results[0].image_name == "app"
        assert results[1].total_downloads == 200

    @responses.activate
    def test_pagination(self, sample_config):
        responses.add(
            responses.GET,
            SEARCH_URL,
            json=_dh_response(
                [_summary("img1", "acme")],
                count=2,
                next_url="https://hub.docker.com/api/content/v1/products/search?page=2&page_size=25&q=bigid",
            ),
            status=200,
        )
        responses.add(
            responses.GET,
            SEARCH_URL,
            json=_dh_response([_summary("img2", "acme")]),
            status=200,
        )
        crawler = DockerHubCrawler(sample_config)
        results = list(crawler.search("bigid"))
        assert len(results) == 2

    @responses.activate
    def test_excludes_owner(self, sample_config):
        responses.add(
            responses.GET,
            SEARCH_URL,
            json=_dh_response([_summary("app", "excluded-org")]),
            status=200,
        )
        crawler = DockerHubCrawler(sample_config)
        assert list(crawler.search("bigid")) == []

    @responses.activate
    def test_skips_empty_name(self, sample_config):
        responses.add(
            responses.GET,
            SEARCH_URL,
            json=_dh_response([_summary("", "acme")]),
            status=200,
        )
        crawler = DockerHubCrawler(sample_config)
        assert list(crawler.search("bigid")) == []

    @responses.activate
    def test_skips_empty_publisher(self, sample_config):
        responses.add(
            responses.GET,
            SEARCH_URL,
            json=_dh_response([_summary("app", "")]),
            status=200,
        )
        crawler = DockerHubCrawler(sample_config)
        assert list(crawler.search("bigid")) == []

    @responses.activate
    def test_zero_count(self, sample_config):
        responses.add(
            responses.GET,
            SEARCH_URL,
            json=_dh_response([], count=0),
            status=200,
        )
        crawler = DockerHubCrawler(sample_config)
        assert list(crawler.search("bigid")) == []

    @responses.activate
    def test_request_failure(self, sample_config):
        responses.add(responses.GET, SEARCH_URL, status=500)
        crawler = DockerHubCrawler(sample_config)
        assert list(crawler.search("bigid")) == []

    @responses.activate
    def test_name_with_slash(self, sample_config):
        """Docker Hub names like 'library/nginx' should use only the part after /."""
        responses.add(
            responses.GET,
            SEARCH_URL,
            json=_dh_response([_summary("library/nginx", "Docker")]),
            status=200,
        )
        crawler = DockerHubCrawler(sample_config)
        results = list(crawler.search("bigid"))
        assert results[0].image_name == "nginx"
        assert results[0].repo_owner == "Docker"

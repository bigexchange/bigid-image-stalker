from __future__ import annotations

import logging
from typing import Iterator
from urllib.parse import parse_qs, urlparse

from container_crawler.crawlers.base import BaseCrawler
from container_crawler.models import ImageResult

logger = logging.getLogger(__name__)

SEARCH_URL = "https://hub.docker.com/api/content/v1/products/search"

COMMON_HEADERS = {
    "Accept": "application/json",
    "Content-Type": "application/json",
    "Search-Version": "v3",
    "X-DOCKER-API-CLIENT": "docker-hub/v3687.0.0",
}


class DockerHubCrawler(BaseCrawler):
    """Crawler for Docker Hub."""

    registry_name = "dockerhub"

    def search(self, term: str) -> Iterator[ImageResult]:
        params: dict = {"page_size": 25, "q": term}

        while True:
            resp = self._get(SEARCH_URL, headers=COMMON_HEADERS, params=params)
            if resp is None:
                logger.error("[dockerhub] Search request failed for term '%s'", term)
                break

            body = resp.json()
            if body.get("count", 0) == 0:
                break

            for item in body.get("summaries", []):
                raw_name = item.get("name", "")
                publisher = item.get("publisher", {}).get("name", "")
                downloads = item.get("pull_count", 0)

                image_name = raw_name.split("/")[-1]
                repo_owner = publisher

                if not image_name or not repo_owner:
                    continue
                if self._is_excluded(repo_owner):
                    logger.debug("[dockerhub] Skipping excluded owner: %s", repo_owner)
                    continue

                yield ImageResult(
                    repo_owner=repo_owner,
                    image_name=image_name,
                    registry="dockerhub",
                    link=f"https://hub.docker.com/r/{repo_owner}/{image_name}",
                    total_downloads=downloads,
                )

            next_url = body.get("next")
            if next_url:
                query_params = parse_qs(urlparse(next_url).query)
                params.update(query_params)
            else:
                break

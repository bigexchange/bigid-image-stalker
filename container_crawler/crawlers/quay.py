from __future__ import annotations

import logging
from typing import Iterator

from container_crawler.crawlers.base import BaseCrawler
from container_crawler.models import ImageResult

logger = logging.getLogger(__name__)

SEARCH_URL = "https://quay.io/api/v1/find/repositories"
REPO_URL_TEMPLATE = "https://quay.io/api/v1/repository/{owner}/{name}"

COMMON_HEADERS = {
    "authority": "quay.io",
    "accept": "application/json",
}


class QuayCrawler(BaseCrawler):
    """Crawler for Quay.io."""

    registry_name = "quay"

    def _get_total_downloads(self, repo_owner: str, image_name: str) -> int | None:
        url = REPO_URL_TEMPLATE.format(owner=repo_owner, name=image_name)
        resp = self._get(url, headers=COMMON_HEADERS, params={"includeStats": True, "includeTags": False})
        if resp is None:
            return None

        stats = resp.json().get("stats", [])
        return sum(s.get("count", 0) for s in stats)

    def search(self, term: str) -> Iterator[ImageResult]:
        params: dict = {"query": term, "page": 1, "includeUsage": True}

        while True:
            resp = self._get(SEARCH_URL, headers=COMMON_HEADERS, params=params)
            if resp is None:
                logger.error("[quay] Search request failed for term '%s'", term)
                break

            body = resp.json()
            results = body.get("results", [])
            if not results:
                break

            for repo in results:
                namespace = repo.get("namespace", {}).get("name", "")
                raw_name = repo.get("name", "")
                image_name = raw_name.split("/")[-1]

                if not image_name or not namespace:
                    continue
                if self._is_excluded(namespace):
                    logger.debug("[quay] Skipping excluded owner: %s", namespace)
                    continue

                downloads = self._get_total_downloads(namespace, image_name)
                if downloads is None:
                    logger.warning("[quay] Could not fetch downloads for %s/%s, skipping", namespace, image_name)
                    continue

                yield ImageResult(
                    repo_owner=namespace,
                    image_name=image_name,
                    registry="quay",
                    link=f"https://quay.io/repository/{namespace}/{image_name}",
                    total_downloads=downloads,
                )

            if not body.get("has_additional"):
                break
            params["page"] += 1

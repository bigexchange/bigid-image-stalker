from __future__ import annotations

import logging
from typing import Iterator

from container_crawler.crawlers.base import BaseCrawler
from container_crawler.models import ImageResult

logger = logging.getLogger(__name__)

SEARCH_URL = "https://api.us-east-1.gallery.ecr.aws/searchRepositoryCatalogData"


class ECRCrawler(BaseCrawler):
    """Crawler for the AWS ECR Public Gallery."""

    registry_name = "ecr"

    def search(self, term: str) -> Iterator[ImageResult]:
        headers = {
            "authority": "api.us-east-1.gallery.ecr.aws",
            "content-type": "application/json",
        }
        payload: dict = {
            "searchTerm": term,
            "sortConfiguration": {"sortKey": "POPULARITY"},
        }

        while True:
            resp = self._post(SEARCH_URL, headers=headers, json=payload)
            if resp is None:
                logger.error("[ecr] Search request failed for term '%s'", term)
                break

            body = resp.json()
            if body.get("totalResults", 0) == 0:
                break

            for repo in body.get("repositoryCatalogSearchResultList", []):
                image_name = repo.get("repositoryName", "")
                repo_owner = repo.get("primaryRegistryAliasName", "")
                downloads = repo.get("downloadCount", 0)

                if not image_name or not repo_owner:
                    continue
                if self._is_excluded(repo_owner):
                    logger.debug("[ecr] Skipping excluded owner: %s", repo_owner)
                    continue

                yield ImageResult(
                    repo_owner=repo_owner,
                    image_name=image_name,
                    registry="ecr",
                    link=f"https://gallery.ecr.aws/{repo_owner}/{image_name}",
                    total_downloads=downloads,
                )

            next_token = body.get("nextToken")
            if next_token:
                payload["nextToken"] = next_token
            else:
                break

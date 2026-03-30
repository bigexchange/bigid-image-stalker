from __future__ import annotations

import abc
import logging
import re
from typing import Iterator

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from container_crawler.config import CrawlerConfig
from container_crawler.models import ImageResult

logger = logging.getLogger(__name__)


class BaseCrawler(abc.ABC):
    """Abstract base class that every registry crawler must implement.

    Subclasses need to implement:
        * ``registry_name`` — class attribute identifying the registry (e.g. ``"ecr"``)
        * ``search`` — yields :class:`ImageResult` objects for each matching image
    """

    registry_name: str = ""

    def __init__(self, config: CrawlerConfig) -> None:
        self.config = config
        self._session = self._build_session()

    def _build_session(self) -> requests.Session:
        session = requests.Session()
        retry = Retry(
            total=self.config.max_retries,
            backoff_factor=self.config.retry_delay,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET", "POST"],
        )
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def _get(self, url: str, **kwargs) -> requests.Response | None:
        kwargs.setdefault("timeout", self.config.request_timeout)
        try:
            resp = self._session.get(url, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            logger.error("GET %s failed: %s", url, exc)
            return None

    def _post(self, url: str, **kwargs) -> requests.Response | None:
        kwargs.setdefault("timeout", self.config.request_timeout)
        try:
            resp = self._session.post(url, **kwargs)
            resp.raise_for_status()
            return resp
        except requests.RequestException as exc:
            logger.error("POST %s failed: %s", url, exc)
            return None

    def _is_excluded(self, owner: str) -> bool:
        return owner.lower() in {o.lower() for o in self.config.exclude_owners}

    @abc.abstractmethod
    def search(self, term: str) -> Iterator[ImageResult]:
        """Yield :class:`ImageResult` for every image matching *term*."""

    def _matches_filter(self, image: ImageResult) -> bool:
        """Return True if the image matches the configured filter pattern (or no filter is set)."""
        pattern = self.config.filter_pattern
        if not pattern:
            return True
        text = f"{image.repo_owner}/{image.image_name}"
        return re.search(pattern, text, re.IGNORECASE) is not None

    def crawl(self) -> list[ImageResult]:
        """Run the crawler for all configured search terms.

        Returns a deduplicated list of :class:`ImageResult`.
        """
        seen: set[str] = set()
        results: list[ImageResult] = []

        for term in self.config.search_terms:
            logger.info("[%s] Searching for '%s'", self.registry_name, term)
            try:
                for image in self.search(term):
                    key = f"{image.registry}:{image.repo_owner}/{image.image_name}"
                    if key in seen:
                        continue
                    seen.add(key)

                    if not self._matches_filter(image):
                        logger.debug(
                            "[%s] Filtered out %s", self.registry_name, image.full_name
                        )
                        continue

                    results.append(image)
                    logger.info(
                        "[%s] Found %s (downloads=%s)",
                        self.registry_name,
                        image.full_name,
                        image.total_downloads,
                    )
            except Exception:
                logger.exception(
                    "[%s] Unexpected error searching for '%s'", self.registry_name, term
                )

        logger.info(
            "[%s] Crawl complete — %d image(s) found", self.registry_name, len(results)
        )
        return results

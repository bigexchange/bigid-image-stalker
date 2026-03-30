from container_crawler.crawlers.base import BaseCrawler
from container_crawler.crawlers.ecr import ECRCrawler
from container_crawler.crawlers.dockerhub import DockerHubCrawler
from container_crawler.crawlers.quay import QuayCrawler

REGISTRY_MAP: dict[str, type[BaseCrawler]] = {
    "ecr": ECRCrawler,
    "dockerhub": DockerHubCrawler,
    "quay": QuayCrawler,
}


def get_crawler(name: str) -> type[BaseCrawler]:
    """Look up a crawler class by registry name.

    Raises ``KeyError`` if the name is not registered.
    """
    return REGISTRY_MAP[name]


def register_crawler(name: str, cls: type[BaseCrawler]) -> None:
    """Register a custom crawler class under *name*."""
    REGISTRY_MAP[name] = cls


__all__ = [
    "BaseCrawler",
    "ECRCrawler",
    "DockerHubCrawler",
    "QuayCrawler",
    "REGISTRY_MAP",
    "get_crawler",
    "register_crawler",
]

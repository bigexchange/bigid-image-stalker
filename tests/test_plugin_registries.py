"""Tests for the plugin registry functions (register_*/get_*) across all subsystems.

Contributors adding a new crawler, storage backend, or notifier should be able
to register it and retrieve it through the public API.
"""

import pytest

from container_crawler.crawlers import REGISTRY_MAP, get_crawler, register_crawler
from container_crawler.crawlers.base import BaseCrawler
from container_crawler.crawlers.ecr import ECRCrawler
from container_crawler.models import ImageResult
from container_crawler.notifications import NOTIFIER_MAP, get_notifier, register_notifier
from container_crawler.notifications.base import BaseNotifier
from container_crawler.notifications.console import ConsoleNotifier
from container_crawler.storage import STORAGE_MAP, get_storage, register_storage
from container_crawler.storage.base import BaseStorage
from container_crawler.storage.dynamodb import DynamoDBStorage


# ---------------------------------------------------------------------------
# Fixtures to isolate module-level registry dicts between tests
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def _restore_crawler_registry():
    original = dict(REGISTRY_MAP)
    yield
    REGISTRY_MAP.clear()
    REGISTRY_MAP.update(original)


@pytest.fixture(autouse=True)
def _restore_storage_registry():
    original = dict(STORAGE_MAP)
    yield
    STORAGE_MAP.clear()
    STORAGE_MAP.update(original)


@pytest.fixture(autouse=True)
def _restore_notifier_registry():
    original = dict(NOTIFIER_MAP)
    yield
    NOTIFIER_MAP.clear()
    NOTIFIER_MAP.update(original)


# ---------------------------------------------------------------------------
# Crawler registry
# ---------------------------------------------------------------------------

class TestCrawlerRegistry:

    def test_get_known_crawler(self):
        assert get_crawler("ecr") is ECRCrawler

    def test_get_unknown_crawler_raises(self):
        with pytest.raises(KeyError):
            get_crawler("nonexistent")

    def test_register_custom_crawler(self, sample_config):
        class DummyCrawler(BaseCrawler):
            registry_name = "dummy"

            def search(self, term):
                return iter([])

        register_crawler("dummy", DummyCrawler)
        assert get_crawler("dummy") is DummyCrawler


# ---------------------------------------------------------------------------
# Storage registry
# ---------------------------------------------------------------------------

class TestStorageRegistry:

    def test_get_known_storage(self):
        assert get_storage("dynamodb") is DynamoDBStorage

    def test_get_unknown_storage_raises(self):
        with pytest.raises(KeyError):
            get_storage("nonexistent")

    def test_register_custom_storage(self):
        class DummyStorage(BaseStorage):
            def exists(self, image):
                return False

            def save(self, image):
                pass

        register_storage("dummy", DummyStorage)
        assert get_storage("dummy") is DummyStorage


# ---------------------------------------------------------------------------
# Notifier registry
# ---------------------------------------------------------------------------

class TestNotifierRegistry:

    def test_get_known_notifier(self):
        assert get_notifier("console") is ConsoleNotifier

    def test_get_unknown_notifier_raises(self):
        with pytest.raises(KeyError):
            get_notifier("nonexistent")

    def test_register_custom_notifier(self):
        class DummyNotifier(BaseNotifier):
            def notify(self, image):
                return True

        register_notifier("dummy", DummyNotifier)
        assert get_notifier("dummy") is DummyNotifier

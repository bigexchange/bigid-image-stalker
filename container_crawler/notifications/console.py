from __future__ import annotations

import logging
from typing import Any

from container_crawler.models import ImageResult
from container_crawler.notifications.base import BaseNotifier

logger = logging.getLogger(__name__)


class ConsoleNotifier(BaseNotifier):
    """Logs new image discoveries to the console — useful for local runs and debugging."""

    def notify(self, image: ImageResult) -> bool:
        logger.info(
            "NEW IMAGE FOUND | registry=%s owner=%s image=%s downloads=%s link=%s",
            image.registry,
            image.repo_owner,
            image.image_name,
            image.total_downloads,
            image.link,
        )
        return True

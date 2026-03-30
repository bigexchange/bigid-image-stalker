from __future__ import annotations

import json
import logging
from typing import Any

import requests

from container_crawler.models import ImageResult
from container_crawler.notifications.base import BaseNotifier

logger = logging.getLogger(__name__)


class SlackNotifier(BaseNotifier):
    """Send notifications to a Slack incoming webhook.

    Options:
        ``webhook_url`` — **required** Slack incoming webhook URL
    """

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        super().__init__(options)
        self._url = self.options.get("webhook_url", "")
        if not self._url:
            raise ValueError("SlackNotifier requires 'webhook_url' in notification_options.slack")

    def notify(self, image: ImageResult) -> bool:
        payload = {
            "text": (
                f"*New container image discovered*\n"
                f"> *Registry:* {image.registry}\n"
                f"> *Owner:* {image.repo_owner}\n"
                f"> *Image:* {image.image_name}\n"
                f"> *Downloads:* {image.total_downloads}\n"
                f"> *Link:* {image.link}"
            )
        }

        try:
            resp = requests.post(
                self._url,
                headers={"Content-Type": "application/json"},
                data=json.dumps(payload),
                timeout=10,
            )
            if resp.status_code == 200:
                logger.debug("Slack notification sent for %s", image.full_name)
                return True
            logger.error("Slack webhook returned %d: %s", resp.status_code, resp.text)
            return False
        except requests.RequestException as exc:
            logger.error("Slack notification failed: %s", exc)
            return False

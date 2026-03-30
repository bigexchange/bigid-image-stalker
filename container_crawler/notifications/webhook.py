from __future__ import annotations

import json
import logging
from typing import Any

import requests

from container_crawler.models import ImageResult
from container_crawler.notifications.base import BaseNotifier

logger = logging.getLogger(__name__)


class WebhookNotifier(BaseNotifier):
    """Send a JSON POST to a generic webhook URL (e.g. Torq, PagerDuty, n8n).

    Options:
        ``url``     — **required** webhook endpoint URL
        ``headers`` — optional dict of extra HTTP headers
        ``secret``  — optional bearer token (sent as ``Authorization: Bearer <secret>``)
    """

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        super().__init__(options)
        self._url = self.options.get("url", "")
        if not self._url:
            raise ValueError(
                "WebhookNotifier requires 'url' in notification_options.webhook"
            )

        self._headers = {"Content-Type": "application/json"}
        if extra := self.options.get("headers"):
            self._headers.update(extra)
        if secret := self.options.get("secret"):
            self._headers["Authorization"] = f"Bearer {secret}"

    def notify(self, image: ImageResult) -> bool:
        payload = image.to_dict()

        try:
            resp = requests.post(
                self._url,
                headers=self._headers,
                data=json.dumps(payload, default=str),
                timeout=10,
            )
            if resp.status_code in range(200, 300):
                logger.debug("Webhook notification sent for %s", image.full_name)
                return True
            logger.error("Webhook returned %d: %s", resp.status_code, resp.text)
            return False
        except requests.RequestException as exc:
            logger.error("Webhook notification failed: %s", exc)
            return False

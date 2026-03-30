from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any

import boto3

from container_crawler.models import ImageResult
from container_crawler.storage.base import BaseStorage

logger = logging.getLogger(__name__)

DEFAULT_TABLE = "ContainerImageCrawlerTable"
DEFAULT_TTL_DAYS = 30


class DynamoDBStorage(BaseStorage):
    """AWS DynamoDB storage backend.

    Requires ``boto3`` (install with ``pip install container-image-crawler[dynamodb]``).

    Options:
        ``table_name`` — DynamoDB table name (default: ``ContainerImageCrawlerTable``)
        ``ttl_days``   — TTL in days for the ``expireDate`` attribute (default: ``30``)
        ``region``     — AWS region (default: from environment / AWS config)
    """

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        super().__init__(options)
        self._table_name = self.options.get("table_name", DEFAULT_TABLE)
        self._ttl_days = int(self.options.get("ttl_days", DEFAULT_TTL_DAYS))

        kwargs: dict[str, Any] = {}
        if region := self.options.get("region"):
            kwargs["region_name"] = region

        self._table = boto3.resource("dynamodb", **kwargs).Table(self._table_name)

    def exists(self, image: ImageResult) -> bool:
        resp = self._table.get_item(
            Key={"repoOwner": image.repo_owner, "imageName": image.image_name}
        )
        return "Item" in resp

    def save(self, image: ImageResult) -> None:
        expire = int((datetime.now(timezone.utc) + timedelta(days=self._ttl_days)).timestamp())
        self._table.put_item(
            Item={
                "repoOwner": image.repo_owner,
                "imageName": image.image_name,
                "imageRegistry": image.registry,
                "link": image.link,
                "totalDownload": image.total_downloads,
                "expireDate": expire,
            }
        )
        logger.debug("Saved %s to DynamoDB table %s", image.full_name, self._table_name)

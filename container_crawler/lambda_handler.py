"""AWS Lambda entry point for the container image crawler.

This module provides a ``handler`` function that can be used as the
Lambda handler.  Configuration is driven entirely by environment variables:

    CRAWLER_SEARCH_TERMS        — comma-separated search terms
    CRAWLER_EXCLUDE_OWNERS      — comma-separated owners to skip
    CRAWLER_REGISTRIES          — comma-separated registries (default: "ecr,dockerhub,quay")
    CRAWLER_FILTER_PATTERN      — optional regex to filter results
    CRAWLER_DYNAMODB_TABLE      — DynamoDB table name (default: "ContainerImageCrawlerTable")
    CRAWLER_DYNAMODB_TTL_DAYS   — TTL in days (default: "30")
    CRAWLER_NOTIFICATION_BACKENDS — comma-separated notifiers (default: "console")
    CRAWLER_SLACK_WEBHOOK_URL   — Slack webhook URL (if using slack notifier)
    CRAWLER_WEBHOOK_URL         — Generic webhook URL (if using webhook notifier)
    CRAWLER_WEBHOOK_SECRET      — Optional bearer token for webhook
    CRAWLER_LOG_LEVEL           — log level (default: "INFO")
"""

from __future__ import annotations

import logging
import os

from container_crawler.config import CrawlerConfig, load_config
from container_crawler.__main__ import run, setup_logging


def handler(event, context):
    """AWS Lambda handler — scans registries and stores new discoveries in DynamoDB."""
    config = load_config()

    # Lambda-specific overrides from environment variables
    table_name = os.environ.get("CRAWLER_DYNAMODB_TABLE", "ContainerImageCrawlerTable")
    ttl_days = os.environ.get("CRAWLER_DYNAMODB_TTL_DAYS", "30")
    config.storage_backend = "dynamodb"
    config.storage_options = {"table_name": table_name, "ttl_days": int(ttl_days)}

    # Notification options from env vars
    if slack_url := os.environ.get("CRAWLER_SLACK_WEBHOOK_URL"):
        config.notification_options["slack"] = {"webhook_url": slack_url}
    if webhook_url := os.environ.get("CRAWLER_WEBHOOK_URL"):
        opts = {"url": webhook_url}
        if secret := os.environ.get("CRAWLER_WEBHOOK_SECRET"):
            opts["secret"] = secret
        config.notification_options["webhook"] = opts

    setup_logging(config.log_level)
    logger = logging.getLogger("container_crawler")

    new_count = run(config)

    logger.info("Lambda execution complete — %d new image(s)", new_count)
    return {"statusCode": 200, "newImages": new_count}

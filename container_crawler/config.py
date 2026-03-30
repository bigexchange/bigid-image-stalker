from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CrawlerConfig:
    """Configuration for the container image crawler."""

    search_terms: list[str] = field(default_factory=list)
    exclude_owners: list[str] = field(default_factory=list)

    registries: list[str] = field(default_factory=lambda: ["ecr", "dockerhub", "quay"])

    storage_backend: str = "dynamodb"
    storage_options: dict[str, Any] = field(default_factory=dict)

    notification_backends: list[str] = field(default_factory=lambda: ["console"])
    notification_options: dict[str, dict[str, Any]] = field(default_factory=dict)

    filter_pattern: str | None = None

    request_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    log_level: str = "INFO"


def load_config(path: str | Path | None = None) -> CrawlerConfig:
    """Load configuration from a YAML file, with environment variable overrides.

    Resolution order (highest priority first):
        1. Environment variables (prefixed with ``CRAWLER_``)
        2. YAML config file
        3. Defaults in :class:`CrawlerConfig`
    """
    raw: dict[str, Any] = {}

    if path is not None:
        p = Path(path)
        if p.exists():
            with open(p) as f:
                raw = yaml.safe_load(f) or {}

    # --- env var overrides ---
    if env_terms := os.environ.get("CRAWLER_SEARCH_TERMS"):
        raw["search_terms"] = [t.strip() for t in env_terms.split(",")]

    if env_exclude := os.environ.get("CRAWLER_EXCLUDE_OWNERS"):
        raw["exclude_owners"] = [o.strip() for o in env_exclude.split(",")]

    if env_registries := os.environ.get("CRAWLER_REGISTRIES"):
        raw["registries"] = [r.strip() for r in env_registries.split(",")]

    if env_storage := os.environ.get("CRAWLER_STORAGE_BACKEND"):
        raw["storage_backend"] = env_storage

    if env_notifiers := os.environ.get("CRAWLER_NOTIFICATION_BACKENDS"):
        raw["notification_backends"] = [n.strip() for n in env_notifiers.split(",")]

    if env_timeout := os.environ.get("CRAWLER_REQUEST_TIMEOUT"):
        raw["request_timeout"] = int(env_timeout)

    if env_retries := os.environ.get("CRAWLER_MAX_RETRIES"):
        raw["max_retries"] = int(env_retries)

    if env_filter := os.environ.get("CRAWLER_FILTER_PATTERN"):
        raw["filter_pattern"] = env_filter

    if env_log := os.environ.get("CRAWLER_LOG_LEVEL"):
        raw["log_level"] = env_log.upper()

    return CrawlerConfig(
        **{k: v for k, v in raw.items() if k in CrawlerConfig.__dataclass_fields__}
    )

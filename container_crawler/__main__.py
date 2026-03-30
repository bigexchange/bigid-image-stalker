"""CLI entry point for the container image crawler.

Usage:
    python -m container_crawler                     # use defaults
    python -m container_crawler -c config.yaml      # use config file
    python -m container_crawler --registries ecr     # override registries
    python -m container_crawler --dry-run            # search only, don't save
"""

from __future__ import annotations

import argparse
import logging
import sys

from container_crawler.config import CrawlerConfig, load_config
from container_crawler.crawlers import get_crawler
from container_crawler.notifications import get_notifier
from container_crawler.storage import get_storage

logger = logging.getLogger("container_crawler")


def setup_logging(level: str) -> None:
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=getattr(logging, level.upper(), logging.INFO),
    )


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="container-crawler",
        description="Scan public container registries for images matching search terms.",
    )
    parser.add_argument("-c", "--config", default=None, help="Path to YAML config file")
    parser.add_argument("--registries", nargs="+", help="Registries to crawl (e.g. ecr dockerhub quay)")
    parser.add_argument("--search-terms", nargs="+", help="Search terms to look for")
    parser.add_argument("--exclude-owners", nargs="+", help="Repository owners to exclude")
    parser.add_argument("--storage", help="Storage backend (dynamodb)")
    parser.add_argument("--filter-pattern", default=None, help="Regex pattern to filter results by owner/image (e.g. 'scanner$', 'myorg-(ui|web)')")
    parser.add_argument("--log-level", default=None, help="Log level (DEBUG, INFO, WARNING, ERROR)")
    parser.add_argument("--dry-run", action="store_true", help="Search only — do not save or notify")
    return parser.parse_args(argv)


def run(config: CrawlerConfig, dry_run: bool = False) -> int:
    """Run the crawler with the given configuration. Returns count of new images found."""
    # Initialize storage
    storage = None
    if not dry_run:
        storage_cls = get_storage(config.storage_backend)
        storage = storage_cls(config.storage_options)

    # Initialize notifiers
    notifiers = []
    if not dry_run:
        for name in config.notification_backends:
            try:
                notifier_cls = get_notifier(name)
                opts = config.notification_options.get(name, {})
                notifiers.append(notifier_cls(opts))
            except (KeyError, ValueError) as exc:
                logger.error("Failed to initialize notifier '%s': %s", name, exc)

    new_count = 0

    try:
        for registry_name in config.registries:
            try:
                crawler_cls = get_crawler(registry_name)
            except KeyError:
                logger.error("Unknown registry: '%s' — skipping", registry_name)
                continue

            crawler = crawler_cls(config)
            results = crawler.crawl()

            for image in results:
                if dry_run:
                    logger.info("[dry-run] Would save: %s from %s", image.full_name, image.registry)
                    new_count += 1
                    continue

                if storage and storage.exists(image):
                    logger.debug("Already exists in storage: %s", image.full_name)
                    continue

                # New discovery
                new_count += 1
                logger.info("New image discovered: %s (%s)", image.full_name, image.registry)

                if storage:
                    storage.save(image)

                for notifier in notifiers:
                    try:
                        notifier.notify(image)
                    except Exception:
                        logger.exception("Notifier %s failed for %s", type(notifier).__name__, image.full_name)
    finally:
        if storage:
            storage.close()

    logger.info("Crawl finished — %d new image(s) discovered", new_count)
    return new_count


def main(argv: list[str] | None = None) -> None:
    args = parse_args(argv)
    config = load_config(args.config)

    # CLI overrides
    if args.registries:
        config.registries = args.registries
    if args.search_terms:
        config.search_terms = args.search_terms
    if args.exclude_owners:
        config.exclude_owners = args.exclude_owners
    if args.storage:
        config.storage_backend = args.storage
    if args.filter_pattern:
        config.filter_pattern = args.filter_pattern
    if args.log_level:
        config.log_level = args.log_level

    setup_logging(config.log_level)
    run(config, dry_run=args.dry_run)


if __name__ == "__main__":
    main()

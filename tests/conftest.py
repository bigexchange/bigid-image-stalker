"""Shared fixtures for the container-image-crawler test suite.

These fixtures provide reusable test data so contributors can focus on writing
test logic rather than constructing setup objects from scratch.
"""

import pytest

from container_crawler.config import CrawlerConfig
from container_crawler.models import ImageResult


@pytest.fixture
def sample_config():
    """A minimal CrawlerConfig suitable for unit tests.

    Uses short timeouts, no retries, and a single search term so crawler
    tests execute quickly without hitting real APIs.
    """
    return CrawlerConfig(
        search_terms=["bigid"],
        exclude_owners=["excluded-org"],
        registries=["ecr", "dockerhub", "quay"],
        storage_backend="dynamodb",
        storage_options={"table_name": "TestTable", "ttl_days": 7},
        notification_backends=["console"],
        notification_options={},
        filter_pattern=None,
        request_timeout=5,
        max_retries=1,
        retry_delay=0.0,
        log_level="DEBUG",
    )


@pytest.fixture
def sample_image():
    """A typical ECR ImageResult for use across test modules."""
    return ImageResult(
        repo_owner="acme",
        image_name="scanner",
        registry="ecr",
        link="https://gallery.ecr.aws/acme/scanner",
        total_downloads=42000,
    )


@pytest.fixture
def sample_image_dockerhub():
    """A typical Docker Hub ImageResult."""
    return ImageResult(
        repo_owner="acme",
        image_name="web-app",
        registry="dockerhub",
        link="https://hub.docker.com/r/acme/web-app",
        total_downloads=100000,
    )


@pytest.fixture
def sample_image_quay():
    """A typical Quay.io ImageResult."""
    return ImageResult(
        repo_owner="redhat",
        image_name="ubi8",
        registry="quay",
        link="https://quay.io/repository/redhat/ubi8",
        total_downloads=5000,
    )

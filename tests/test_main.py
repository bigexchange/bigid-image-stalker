"""Tests for container_crawler.__main__ — CLI parsing, run() orchestration, and main()."""

from unittest.mock import MagicMock, patch

from container_crawler.__main__ import main, parse_args, run
from container_crawler.config import CrawlerConfig


# ---------------------------------------------------------------------------
# parse_args
# ---------------------------------------------------------------------------


class TestParseArgs:
    def test_defaults(self):
        args = parse_args([])
        assert args.config is None
        assert args.dry_run is False
        assert args.registries is None
        assert args.search_terms is None

    def test_config_flag(self):
        args = parse_args(["-c", "my.yaml"])
        assert args.config == "my.yaml"

    def test_registries(self):
        args = parse_args(["--registries", "ecr", "quay"])
        assert args.registries == ["ecr", "quay"]

    def test_search_terms(self):
        args = parse_args(["--search-terms", "a", "b"])
        assert args.search_terms == ["a", "b"]

    def test_dry_run(self):
        args = parse_args(["--dry-run"])
        assert args.dry_run is True

    def test_filter_pattern(self):
        args = parse_args(["--filter-pattern", "scanner$"])
        assert args.filter_pattern == "scanner$"

    def test_storage(self):
        args = parse_args(["--storage", "dynamodb"])
        assert args.storage == "dynamodb"

    def test_log_level(self):
        args = parse_args(["--log-level", "DEBUG"])
        assert args.log_level == "DEBUG"


# ---------------------------------------------------------------------------
# run()
# ---------------------------------------------------------------------------


def _make_mock_crawler(results):
    """Return a mock crawler class whose instances .crawl() returns *results*."""
    mock_cls = MagicMock()
    mock_cls.return_value.crawl.return_value = results
    return mock_cls


class TestRun:
    @patch("container_crawler.__main__.get_crawler")
    def test_dry_run(self, mock_get_crawler, sample_config, sample_image):
        mock_get_crawler.return_value = _make_mock_crawler([sample_image])
        sample_config.registries = ["ecr"]
        count = run(sample_config, dry_run=True)
        assert count == 1

    @patch("container_crawler.__main__.get_notifier")
    @patch("container_crawler.__main__.get_storage")
    @patch("container_crawler.__main__.get_crawler")
    def test_new_image_saved_and_notified(
        self,
        mock_get_crawler,
        mock_get_storage,
        mock_get_notifier,
        sample_config,
        sample_image,
    ):
        mock_get_crawler.return_value = _make_mock_crawler([sample_image])
        mock_storage = MagicMock()
        mock_storage.exists.return_value = False
        mock_get_storage.return_value.return_value = mock_storage
        mock_notifier = MagicMock()
        mock_notifier.notify.return_value = True
        mock_get_notifier.return_value.return_value = mock_notifier

        sample_config.registries = ["ecr"]
        count = run(sample_config, dry_run=False)

        assert count == 1
        mock_storage.save.assert_called_once_with(sample_image)
        mock_notifier.notify.assert_called_once_with(sample_image)

    @patch("container_crawler.__main__.get_notifier")
    @patch("container_crawler.__main__.get_storage")
    @patch("container_crawler.__main__.get_crawler")
    def test_existing_image_skipped(
        self,
        mock_get_crawler,
        mock_get_storage,
        mock_get_notifier,
        sample_config,
        sample_image,
    ):
        mock_get_crawler.return_value = _make_mock_crawler([sample_image])
        mock_storage = MagicMock()
        mock_storage.exists.return_value = True
        mock_get_storage.return_value.return_value = mock_storage

        sample_config.registries = ["ecr"]
        count = run(sample_config, dry_run=False)

        assert count == 0
        mock_storage.save.assert_not_called()

    @patch("container_crawler.__main__.get_crawler")
    def test_unknown_registry_skipped(self, mock_get_crawler, sample_config):
        mock_get_crawler.side_effect = KeyError("nonexistent")
        sample_config.registries = ["nonexistent"]
        count = run(sample_config, dry_run=True)
        assert count == 0

    @patch("container_crawler.__main__.get_notifier")
    @patch("container_crawler.__main__.get_storage")
    @patch("container_crawler.__main__.get_crawler")
    def test_notifier_exception_caught(
        self,
        mock_get_crawler,
        mock_get_storage,
        mock_get_notifier,
        sample_config,
        sample_image,
    ):
        mock_get_crawler.return_value = _make_mock_crawler([sample_image])
        mock_storage = MagicMock()
        mock_storage.exists.return_value = False
        mock_get_storage.return_value.return_value = mock_storage
        mock_notifier = MagicMock()
        mock_notifier.notify.side_effect = RuntimeError("notification boom")
        mock_get_notifier.return_value.return_value = mock_notifier

        sample_config.registries = ["ecr"]
        # Should not crash.
        count = run(sample_config, dry_run=False)
        assert count == 1

    @patch("container_crawler.__main__.get_storage")
    @patch("container_crawler.__main__.get_crawler")
    def test_storage_closed(self, mock_get_crawler, mock_get_storage, sample_config):
        mock_get_crawler.return_value = _make_mock_crawler([])
        mock_storage = MagicMock()
        mock_get_storage.return_value.return_value = mock_storage

        sample_config.registries = ["ecr"]
        run(sample_config, dry_run=False)
        mock_storage.close.assert_called_once()


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------


class TestMain:
    @patch("container_crawler.__main__.run")
    @patch("container_crawler.__main__.load_config")
    def test_cli_overrides(self, mock_load_config, mock_run):
        mock_load_config.return_value = CrawlerConfig()
        main(["--registries", "ecr", "--search-terms", "bigid", "--dry-run"])

        config = mock_run.call_args[0][0]
        assert config.registries == ["ecr"]
        assert config.search_terms == ["bigid"]
        assert (
            mock_run.call_args[1]["dry_run"] is True or mock_run.call_args[0][1] is True
        )

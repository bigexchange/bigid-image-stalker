"""Tests for container_crawler.lambda_handler.

All external dependencies (load_config, run, setup_logging) are mocked so
these tests can run without AWS credentials.
"""

from unittest.mock import patch, MagicMock

from container_crawler.config import CrawlerConfig


@patch("container_crawler.lambda_handler.run", return_value=3)
@patch("container_crawler.lambda_handler.setup_logging")
@patch("container_crawler.lambda_handler.load_config")
class TestLambdaHandler:

    def test_returns_status_and_count(self, mock_load_config, mock_setup, mock_run):
        mock_load_config.return_value = CrawlerConfig()
        from container_crawler.lambda_handler import handler

        result = handler({}, None)
        assert result == {"statusCode": 200, "newImages": 3}

    def test_forces_dynamodb_storage(self, mock_load_config, mock_setup, mock_run):
        mock_load_config.return_value = CrawlerConfig(storage_backend="postgres")
        from container_crawler.lambda_handler import handler

        handler({}, None)
        config = mock_run.call_args[0][0]
        assert config.storage_backend == "dynamodb"

    def test_dynamodb_table_from_env(self, mock_load_config, mock_setup, mock_run, monkeypatch):
        monkeypatch.setenv("CRAWLER_DYNAMODB_TABLE", "MyTable")
        mock_load_config.return_value = CrawlerConfig()
        from container_crawler.lambda_handler import handler

        handler({}, None)
        config = mock_run.call_args[0][0]
        assert config.storage_options["table_name"] == "MyTable"

    def test_ttl_days_from_env(self, mock_load_config, mock_setup, mock_run, monkeypatch):
        monkeypatch.setenv("CRAWLER_DYNAMODB_TTL_DAYS", "90")
        mock_load_config.return_value = CrawlerConfig()
        from container_crawler.lambda_handler import handler

        handler({}, None)
        config = mock_run.call_args[0][0]
        assert config.storage_options["ttl_days"] == 90

    def test_slack_webhook_from_env(self, mock_load_config, mock_setup, mock_run, monkeypatch):
        monkeypatch.setenv("CRAWLER_SLACK_WEBHOOK_URL", "https://hooks.slack.com/x")
        mock_load_config.return_value = CrawlerConfig()
        from container_crawler.lambda_handler import handler

        handler({}, None)
        config = mock_run.call_args[0][0]
        assert config.notification_options["slack"]["webhook_url"] == "https://hooks.slack.com/x"

    def test_webhook_url_and_secret_from_env(self, mock_load_config, mock_setup, mock_run, monkeypatch):
        monkeypatch.setenv("CRAWLER_WEBHOOK_URL", "https://example.com/hook")
        monkeypatch.setenv("CRAWLER_WEBHOOK_SECRET", "s3cret")
        mock_load_config.return_value = CrawlerConfig()
        from container_crawler.lambda_handler import handler

        handler({}, None)
        config = mock_run.call_args[0][0]
        assert config.notification_options["webhook"]["url"] == "https://example.com/hook"
        assert config.notification_options["webhook"]["secret"] == "s3cret"

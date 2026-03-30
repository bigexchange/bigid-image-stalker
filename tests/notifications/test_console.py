"""Tests for container_crawler.notifications.console.ConsoleNotifier."""

import logging

from container_crawler.notifications.console import ConsoleNotifier


class TestConsoleNotifier:

    def test_notify_returns_true(self, sample_image):
        notifier = ConsoleNotifier()
        assert notifier.notify(sample_image) is True

    def test_notify_logs_message(self, sample_image, caplog):
        notifier = ConsoleNotifier()
        with caplog.at_level(logging.INFO):
            notifier.notify(sample_image)
        assert "NEW IMAGE FOUND" in caplog.text
        assert "acme" in caplog.text
        assert "scanner" in caplog.text
        assert "ecr" in caplog.text

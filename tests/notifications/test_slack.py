"""Tests for container_crawler.notifications.slack.SlackNotifier."""

import json

import pytest
import requests
import responses

from container_crawler.notifications.slack import SlackNotifier

WEBHOOK_URL = "https://hooks.slack.com/services/T00/B00/xxx"


class TestSlackInit:
    def test_raises_without_webhook_url(self):
        with pytest.raises(ValueError, match="webhook_url"):
            SlackNotifier({})

    def test_raises_with_empty_url(self):
        with pytest.raises(ValueError, match="webhook_url"):
            SlackNotifier({"webhook_url": ""})

    def test_accepts_valid_url(self):
        notifier = SlackNotifier({"webhook_url": WEBHOOK_URL})
        assert notifier._url == WEBHOOK_URL


class TestSlackNotify:
    @responses.activate
    def test_success(self, sample_image):
        responses.add(responses.POST, WEBHOOK_URL, status=200)
        notifier = SlackNotifier({"webhook_url": WEBHOOK_URL})
        assert notifier.notify(sample_image) is True

    @responses.activate
    def test_payload_format(self, sample_image):
        responses.add(responses.POST, WEBHOOK_URL, status=200)
        notifier = SlackNotifier({"webhook_url": WEBHOOK_URL})
        notifier.notify(sample_image)

        body = json.loads(responses.calls[0].request.body)
        assert "text" in body
        assert "scanner" in body["text"]
        assert "acme" in body["text"]
        assert "ecr" in body["text"]

    @responses.activate
    def test_non_200_returns_false(self, sample_image):
        responses.add(responses.POST, WEBHOOK_URL, status=400)
        notifier = SlackNotifier({"webhook_url": WEBHOOK_URL})
        assert notifier.notify(sample_image) is False

    @responses.activate
    def test_connection_error_returns_false(self, sample_image):
        responses.add(
            responses.POST,
            WEBHOOK_URL,
            body=requests.ConnectionError("network down"),
        )
        notifier = SlackNotifier({"webhook_url": WEBHOOK_URL})
        assert notifier.notify(sample_image) is False

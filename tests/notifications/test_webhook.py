"""Tests for container_crawler.notifications.webhook.WebhookNotifier."""

import json

import pytest
import requests
import responses

from container_crawler.notifications.webhook import WebhookNotifier

WEBHOOK_URL = "https://example.com/webhook"


class TestWebhookInit:
    def test_raises_without_url(self):
        with pytest.raises(ValueError, match="url"):
            WebhookNotifier({})

    def test_raises_with_empty_url(self):
        with pytest.raises(ValueError, match="url"):
            WebhookNotifier({"url": ""})

    def test_sets_bearer_token(self):
        notifier = WebhookNotifier({"url": WEBHOOK_URL, "secret": "tok123"})
        assert notifier._headers["Authorization"] == "Bearer tok123"

    def test_merges_custom_headers(self):
        notifier = WebhookNotifier({"url": WEBHOOK_URL, "headers": {"X-Custom": "v"}})
        assert notifier._headers["X-Custom"] == "v"
        assert notifier._headers["Content-Type"] == "application/json"


class TestWebhookNotify:
    @responses.activate
    def test_success_200(self, sample_image):
        responses.add(responses.POST, WEBHOOK_URL, status=200)
        notifier = WebhookNotifier({"url": WEBHOOK_URL})
        assert notifier.notify(sample_image) is True

    @responses.activate
    def test_success_201(self, sample_image):
        responses.add(responses.POST, WEBHOOK_URL, status=201)
        notifier = WebhookNotifier({"url": WEBHOOK_URL})
        assert notifier.notify(sample_image) is True

    @responses.activate
    def test_sends_to_dict_payload(self, sample_image):
        responses.add(responses.POST, WEBHOOK_URL, status=200)
        notifier = WebhookNotifier({"url": WEBHOOK_URL})
        notifier.notify(sample_image)

        body = json.loads(responses.calls[0].request.body)
        expected = sample_image.to_dict()
        assert body == expected

    @responses.activate
    def test_failure_400(self, sample_image):
        responses.add(responses.POST, WEBHOOK_URL, status=400)
        notifier = WebhookNotifier({"url": WEBHOOK_URL})
        assert notifier.notify(sample_image) is False

    @responses.activate
    def test_connection_error(self, sample_image):
        responses.add(
            responses.POST,
            WEBHOOK_URL,
            body=requests.ConnectionError("network down"),
        )
        notifier = WebhookNotifier({"url": WEBHOOK_URL})
        assert notifier.notify(sample_image) is False

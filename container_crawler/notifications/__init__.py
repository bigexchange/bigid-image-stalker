from container_crawler.notifications.base import BaseNotifier
from container_crawler.notifications.console import ConsoleNotifier
from container_crawler.notifications.slack import SlackNotifier
from container_crawler.notifications.webhook import WebhookNotifier

NOTIFIER_MAP: dict[str, type[BaseNotifier]] = {
    "console": ConsoleNotifier,
    "slack": SlackNotifier,
    "webhook": WebhookNotifier,
}


def get_notifier(name: str) -> type[BaseNotifier]:
    """Look up a notifier class by name.

    Raises ``KeyError`` if the name is not registered.
    """
    return NOTIFIER_MAP[name]


def register_notifier(name: str, cls: type[BaseNotifier]) -> None:
    """Register a custom notifier under *name*."""
    NOTIFIER_MAP[name] = cls


__all__ = [
    "BaseNotifier",
    "ConsoleNotifier",
    "SlackNotifier",
    "WebhookNotifier",
    "NOTIFIER_MAP",
    "get_notifier",
    "register_notifier",
]

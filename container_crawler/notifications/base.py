from __future__ import annotations

import abc
from typing import Any

from container_crawler.models import ImageResult


class BaseNotifier(abc.ABC):
    """Abstract base class for notification backends.

    Subclasses must implement ``notify``.
    """

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        self.options = options or {}

    @abc.abstractmethod
    def notify(self, image: ImageResult) -> bool:
        """Send a notification about a newly discovered *image*.

        Returns ``True`` on success, ``False`` on failure.
        """

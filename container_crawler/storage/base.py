from __future__ import annotations

import abc
from typing import Any

from container_crawler.models import ImageResult


class BaseStorage(abc.ABC):
    """Abstract base class for storage backends.

    Subclasses must implement ``exists``, ``save``, and ``close``.
    """

    def __init__(self, options: dict[str, Any] | None = None) -> None:
        self.options = options or {}

    @abc.abstractmethod
    def exists(self, image: ImageResult) -> bool:
        """Return ``True`` if an entry for *image* already exists."""

    @abc.abstractmethod
    def save(self, image: ImageResult) -> None:
        """Persist *image* to the storage backend."""

    def close(self) -> None:
        """Release any resources held by the backend."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()

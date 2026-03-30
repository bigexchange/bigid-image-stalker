from container_crawler.storage.base import BaseStorage
from container_crawler.storage.dynamodb import DynamoDBStorage

STORAGE_MAP: dict[str, type[BaseStorage]] = {
    "dynamodb": DynamoDBStorage,
}


def get_storage(name: str) -> type[BaseStorage]:
    """Look up a storage backend class by name.

    Raises ``KeyError`` if the name is not registered.
    """
    return STORAGE_MAP[name]


def register_storage(name: str, cls: type[BaseStorage]) -> None:
    """Register a custom storage backend under *name*."""
    STORAGE_MAP[name] = cls


__all__ = [
    "BaseStorage",
    "DynamoDBStorage",
    "STORAGE_MAP",
    "get_storage",
    "register_storage",
]

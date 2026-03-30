from __future__ import annotations

from dataclasses import dataclass, field, asdict


@dataclass
class ImageResult:
    """Represents a discovered container image from a registry search."""

    repo_owner: str
    image_name: str
    registry: str
    link: str
    total_downloads: int = 0
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        d = asdict(self)
        d.pop("extra", None)
        d.update(self.extra)
        return d

    @property
    def full_name(self) -> str:
        return f"{self.repo_owner}/{self.image_name}"

"""Tests for container_crawler.models.ImageResult."""

from container_crawler.models import ImageResult


class TestImageResult:
    """Verify ImageResult dataclass behaviour — serialisation, defaults, and properties."""

    def test_full_name(self, sample_image):
        assert sample_image.full_name == "acme/scanner"

    def test_to_dict_basic(self, sample_image):
        d = sample_image.to_dict()
        assert d["repo_owner"] == "acme"
        assert d["image_name"] == "scanner"
        assert d["registry"] == "ecr"
        assert d["link"] == "https://gallery.ecr.aws/acme/scanner"
        assert d["total_downloads"] == 42000
        # The `extra` key itself should not appear in the output dict.
        assert "extra" not in d

    def test_to_dict_with_extra(self):
        image = ImageResult(
            repo_owner="acme",
            image_name="scanner",
            registry="ecr",
            link="https://example.com",
            extra={"custom_field": "val"},
        )
        d = image.to_dict()
        assert d["custom_field"] == "val"
        assert "extra" not in d

    def test_to_dict_extra_overrides_base_field(self):
        """Extra keys that collide with base fields overwrite them in to_dict()."""
        image = ImageResult(
            repo_owner="acme",
            image_name="scanner",
            registry="ecr",
            link="https://example.com",
            extra={"registry": "overridden"},
        )
        d = image.to_dict()
        assert d["registry"] == "overridden"

    def test_default_downloads_zero(self):
        image = ImageResult(
            repo_owner="a", image_name="b", registry="ecr", link="https://x"
        )
        assert image.total_downloads == 0

    def test_default_extra_empty_dict(self):
        image = ImageResult(
            repo_owner="a", image_name="b", registry="ecr", link="https://x"
        )
        assert image.extra == {}

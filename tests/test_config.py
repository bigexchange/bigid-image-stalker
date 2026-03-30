"""Tests for container_crawler.config — CrawlerConfig defaults, YAML loading, and env overrides."""

import yaml

from container_crawler.config import load_config


class TestDefaults:
    """CrawlerConfig should have sensible defaults when nothing is provided."""

    def test_defaults(self):
        config = load_config(None)
        assert config.search_terms == []
        assert config.exclude_owners == []
        assert config.registries == ["ecr", "dockerhub", "quay"]
        assert config.storage_backend == "dynamodb"
        assert config.notification_backends == ["console"]
        assert config.filter_pattern is None
        assert config.request_timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.log_level == "INFO"


class TestYAMLLoading:
    """load_config should read values from a YAML file."""

    def test_load_from_yaml(self, tmp_path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(
            yaml.dump(
                {
                    "search_terms": ["term1", "term2"],
                    "registries": ["ecr"],
                    "log_level": "DEBUG",
                }
            )
        )
        config = load_config(str(cfg_file))
        assert config.search_terms == ["term1", "term2"]
        assert config.registries == ["ecr"]
        assert config.log_level == "DEBUG"

    def test_load_nonexistent_yaml(self, tmp_path):
        config = load_config(str(tmp_path / "nope.yaml"))
        # Should fall back to defaults without crashing.
        assert config.registries == ["ecr", "dockerhub", "quay"]

    def test_unknown_yaml_keys_ignored(self, tmp_path):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump({"unknown_field": 123, "search_terms": ["x"]}))
        config = load_config(str(cfg_file))
        assert config.search_terms == ["x"]
        assert not hasattr(config, "unknown_field")


class TestEnvOverrides:
    """Environment variables prefixed with CRAWLER_ should take priority."""

    def test_search_terms(self, monkeypatch):
        monkeypatch.setenv("CRAWLER_SEARCH_TERMS", "a,b,c")
        config = load_config(None)
        assert config.search_terms == ["a", "b", "c"]

    def test_exclude_owners(self, monkeypatch):
        monkeypatch.setenv("CRAWLER_EXCLUDE_OWNERS", "org1,org2")
        config = load_config(None)
        assert config.exclude_owners == ["org1", "org2"]

    def test_registries(self, monkeypatch):
        monkeypatch.setenv("CRAWLER_REGISTRIES", "ecr,quay")
        config = load_config(None)
        assert config.registries == ["ecr", "quay"]

    def test_storage_backend(self, monkeypatch):
        monkeypatch.setenv("CRAWLER_STORAGE_BACKEND", "postgres")
        config = load_config(None)
        assert config.storage_backend == "postgres"

    def test_notification_backends(self, monkeypatch):
        monkeypatch.setenv("CRAWLER_NOTIFICATION_BACKENDS", "slack,webhook")
        config = load_config(None)
        assert config.notification_backends == ["slack", "webhook"]

    def test_request_timeout(self, monkeypatch):
        monkeypatch.setenv("CRAWLER_REQUEST_TIMEOUT", "10")
        config = load_config(None)
        assert config.request_timeout == 10

    def test_max_retries(self, monkeypatch):
        monkeypatch.setenv("CRAWLER_MAX_RETRIES", "5")
        config = load_config(None)
        assert config.max_retries == 5

    def test_filter_pattern(self, monkeypatch):
        monkeypatch.setenv("CRAWLER_FILTER_PATTERN", "scanner$")
        config = load_config(None)
        assert config.filter_pattern == "scanner$"

    def test_log_level_uppercased(self, monkeypatch):
        monkeypatch.setenv("CRAWLER_LOG_LEVEL", "debug")
        config = load_config(None)
        assert config.log_level == "DEBUG"

    def test_env_overrides_yaml(self, tmp_path, monkeypatch):
        cfg_file = tmp_path / "config.yaml"
        cfg_file.write_text(yaml.dump({"search_terms": ["from_yaml"]}))
        monkeypatch.setenv("CRAWLER_SEARCH_TERMS", "from_env")
        config = load_config(str(cfg_file))
        assert config.search_terms == ["from_env"]

"""Tests for container_crawler.storage.dynamodb.DynamoDBStorage.

boto3 is fully mocked — no AWS credentials or network access required.
"""

import time
from unittest.mock import MagicMock, patch

from container_crawler.storage.dynamodb import DEFAULT_TABLE, DEFAULT_TTL_DAYS, DynamoDBStorage


@patch("container_crawler.storage.dynamodb.boto3")
class TestDynamoDBInit:

    def test_defaults(self, mock_boto3):
        DynamoDBStorage()
        mock_boto3.resource.return_value.Table.assert_called_once_with(DEFAULT_TABLE)

    def test_custom_table(self, mock_boto3):
        DynamoDBStorage({"table_name": "CustomTable"})
        mock_boto3.resource.return_value.Table.assert_called_once_with("CustomTable")

    def test_custom_region(self, mock_boto3):
        DynamoDBStorage({"region": "eu-west-1"})
        mock_boto3.resource.assert_called_once_with("dynamodb", region_name="eu-west-1")


@patch("container_crawler.storage.dynamodb.boto3")
class TestDynamoDBExists:

    def test_exists_true(self, mock_boto3, sample_image):
        mock_table = MagicMock()
        mock_boto3.resource.return_value.Table.return_value = mock_table
        mock_table.get_item.return_value = {"Item": {"repoOwner": "acme"}}

        storage = DynamoDBStorage({"table_name": "T"})
        assert storage.exists(sample_image) is True

    def test_exists_false(self, mock_boto3, sample_image):
        mock_table = MagicMock()
        mock_boto3.resource.return_value.Table.return_value = mock_table
        mock_table.get_item.return_value = {}

        storage = DynamoDBStorage({"table_name": "T"})
        assert storage.exists(sample_image) is False

    def test_key_structure(self, mock_boto3, sample_image):
        mock_table = MagicMock()
        mock_boto3.resource.return_value.Table.return_value = mock_table
        mock_table.get_item.return_value = {}

        storage = DynamoDBStorage({"table_name": "T"})
        storage.exists(sample_image)
        mock_table.get_item.assert_called_once_with(
            Key={"repoOwner": "acme", "imageName": "scanner"}
        )


@patch("container_crawler.storage.dynamodb.boto3")
class TestDynamoDBSave:

    def test_item_structure(self, mock_boto3, sample_image):
        mock_table = MagicMock()
        mock_boto3.resource.return_value.Table.return_value = mock_table

        storage = DynamoDBStorage({"table_name": "T", "ttl_days": 7})
        storage.save(sample_image)

        call_args = mock_table.put_item.call_args
        item = call_args[1]["Item"] if "Item" in call_args[1] else call_args[0][0]
        assert item["repoOwner"] == "acme"
        assert item["imageName"] == "scanner"
        assert item["imageRegistry"] == "ecr"
        assert item["link"] == "https://gallery.ecr.aws/acme/scanner"
        assert item["totalDownload"] == 42000
        assert "expireDate" in item

    def test_ttl_calculation(self, mock_boto3, sample_image):
        mock_table = MagicMock()
        mock_boto3.resource.return_value.Table.return_value = mock_table

        storage = DynamoDBStorage({"table_name": "T", "ttl_days": 7})
        storage.save(sample_image)

        item = mock_table.put_item.call_args[1]["Item"]
        expected_min = int(time.time()) + 7 * 86400 - 60
        expected_max = int(time.time()) + 7 * 86400 + 60
        assert expected_min <= item["expireDate"] <= expected_max


@patch("container_crawler.storage.dynamodb.boto3")
class TestDynamoDBContextManager:

    def test_context_manager(self, mock_boto3):
        with DynamoDBStorage({"table_name": "T"}) as storage:
            assert storage is not None

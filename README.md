# Container Image Crawler

A modular, extensible tool for scanning public container registries for images matching configurable search terms. Supports ECR Public, Docker Hub, and Quay.io out of the box, with a plugin architecture for adding custom registries and notification channels.

## Quick Start

```bash
# Install
pip install -e .

# Dry run — search only, don't save or notify
container-crawler --search-terms mycompany --dry-run

# Run with a config file
container-crawler -c config.yaml

# Override via CLI
container-crawler --registries ecr dockerhub --search-terms mycompany

# Filter results with regex
container-crawler --search-terms mycompany --filter-pattern "scanner$" --dry-run
```

## Configuration

Configuration is loaded with the following priority (highest first):

1. **CLI flags** (`--registries`, `--search-terms`, etc.)
2. **Environment variables** (prefixed with `CRAWLER_`)
3. **YAML config file** (passed via `-c`)
4. **Defaults**

Copy `config.example.yaml` to `config.yaml` and adjust as needed.

### Environment Variables

| Variable | Description | Example |
|---|---|---|
| `CRAWLER_SEARCH_TERMS` | Comma-separated search terms | `mycompany,myorg` |
| `CRAWLER_EXCLUDE_OWNERS` | Comma-separated owners to skip | `myorg-official` |
| `CRAWLER_REGISTRIES` | Comma-separated registries | `ecr,dockerhub,quay` |
| `CRAWLER_FILTER_PATTERN` | Regex to filter results | `scanner$` |
| `CRAWLER_STORAGE_BACKEND` | Storage backend name | `dynamodb` |
| `CRAWLER_NOTIFICATION_BACKENDS` | Comma-separated notifiers | `console,slack` |
| `CRAWLER_LOG_LEVEL` | Log level | `DEBUG` |

### CLI Flags

```
--search-terms        Search terms to look for
--exclude-owners      Repository owners to exclude
--registries          Registries to crawl (ecr, dockerhub, quay)
--filter-pattern      Regex pattern to filter results by owner/image
--storage             Storage backend (dynamodb)
--log-level           Log level (DEBUG, INFO, WARNING, ERROR)
--dry-run             Search only — do not save or notify
-c, --config          Path to YAML config file
```

## Supported Registries

| Registry | Name | API |
|---|---|---|
| AWS ECR Public Gallery | `ecr` | POST-based search |
| Docker Hub | `dockerhub` | Content search API v3 |
| Quay.io | `quay` | Repository search + stats API |

## Storage

Results are stored in **AWS DynamoDB**. The DynamoDB table must already exist before running the crawler. If deploying via the included CloudFormation template, the table is created automatically. Otherwise, create a table with the following schema:

- **Table name:** `ContainerImageCrawlerTable` (configurable)
- **Partition key:** `repoOwner` (String)
- **Sort key:** `imageName` (String)
- **TTL attribute:** `expireDate`

### Required IAM Permissions

The IAM user or role running the crawler needs the following permissions on the DynamoDB table:

```
dynamodb:GetItem
dynamodb:PutItem
dynamodb:UpdateItem
dynamodb:Query
```

### Storage Options

Configurable via config file or environment variables:

| Option | Default | Description |
|---|---|---|
| `table_name` | `ContainerImageCrawlerTable` | DynamoDB table name |
| `ttl_days` | `30` | Days before entries expire |
| `region` | From AWS config | AWS region |

## Notification Backends

| Backend | Name | Description |
|---|---|---|
| Console | `console` | Logs to stdout (default) |
| Slack | `slack` | Slack incoming webhook |
| Webhook | `webhook` | Generic JSON POST (e.g. PagerDuty, n8n, Torq) |

## AWS Deployment (CloudFormation)

A ready-to-deploy CloudFormation template is included. It provisions:

- **DynamoDB table** with TTL
- **Lambda function** (Python 3.12) running all crawlers
- **EventBridge rule** for scheduled execution
- **IAM role** with least-privilege permissions
- **CloudWatch Log Group**

### Deploy

1. Package the code as a zip and upload to S3:
```bash
cd opensource
zip -r package.zip container_crawler/ -x '*__pycache__*'
aws s3 cp package.zip s3://my-bucket/crawler/package.zip
```

2. Deploy the stack:
```bash
aws cloudformation deploy \
  --template-file cloudformation.yaml \
  --stack-name container-image-crawler \
  --parameter-overrides \
      S3Bucket=my-bucket \
      S3Key=crawler/package.zip \
      SearchTerms=mycompany \
      ExcludeOwners=myorg \
      ScheduleExpression="rate(1 day)" \
  --capabilities CAPABILITY_NAMED_IAM
```

All crawler settings are configurable as CloudFormation parameters — see `cloudformation.yaml` for the full list.

## Regex Filtering

Use `--filter-pattern` to apply a regex filter on results after they come back from the registry APIs. The pattern is matched (case-insensitive) against `owner/image_name`.

```bash
# Only images ending in "scanner"
container-crawler --search-terms mycompany --filter-pattern "scanner$" --dry-run

# Images matching "mycompany-ui" or "mycompany-web"
container-crawler --search-terms mycompany --filter-pattern "mycompany-(ui|web)" --dry-run
```

## Extending

### Adding a Custom Registry

```python
from container_crawler.crawlers.base import BaseCrawler
from container_crawler.crawlers import register_crawler
from container_crawler.models import ImageResult

class GitHubCrawler(BaseCrawler):
    registry_name = "ghcr"

    def search(self, term: str):
        # Implement your registry-specific search logic here.
        # Yield ImageResult objects for each matching image.
        yield ImageResult(
            repo_owner="owner",
            image_name="image",
            registry=self.registry_name,
            link="https://ghcr.io/owner/image",
        )

register_crawler("ghcr", GitHubCrawler)
```

### Adding a Custom Storage Backend

```python
from container_crawler.storage.base import BaseStorage
from container_crawler.storage import register_storage

class PostgresStorage(BaseStorage):
    def exists(self, image):
        # Check if image exists in your database
        ...

    def save(self, image):
        # Persist the image record
        ...

register_storage("postgres", PostgresStorage)
```

### Adding a Custom Notifier

```python
from container_crawler.notifications.base import BaseNotifier
from container_crawler.notifications import register_notifier

class EmailNotifier(BaseNotifier):
    def notify(self, image):
        # Send an email about the new image
        ...
        return True

register_notifier("email", EmailNotifier)
```

## Using from Python

```python
from container_crawler.config import load_config
from container_crawler.__main__ import run

config = load_config("config.yaml")
new_count = run(config)
print(f"Found {new_count} new images")
```

## Development

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT

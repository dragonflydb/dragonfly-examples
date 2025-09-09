## Feast with DuckDB & DragonflyDB for Recommendation System Example

This repository showcases a complete example of building a simple feature store for a recommendation system using Feast
with DuckDB as the offline store and Dragonfly as the Redis-compatible high-performance online store.

This current repository is called a feature repository for Feast.
We configure the feature store in `feature_store.yaml`, generating sample Parquet data representing users, items,
and their interactions, and defining feature views and entities in a Python repository file.
The repository demonstrates how to retrieve historical offline features with point-in-time correctness using timestamps
and how to serve real-time online features for model inference. We also cover best practices for materializing features
into the online store and managing timestamps with UTC awareness, and thus using Feast effectively for both offline
training and online serving in recommendation systems.

## How to Run

- First of all, let's make sure a Dragonfly server instance is running locally:

```bash
docker run -p 6379:6379 --ulimit memlock=-1 docker.dragonflydb.io/dragonflydb/dragonfly
````

- Let's use [`uv`](https://github.com/astral-sh/uv) as our Python package and project manager.

```bash
# Install uv with curl:
$> curl -LsSf https://astral.sh/uv/install.sh | sh

# Install uv with wget:
$> wget -qO- https://astral.sh/uv/install.sh | sh
```

- Make sure commands below are executed within the current project's directory (`dragonfly-examples/feast-recommendation`).

```bash
$> cd /PATH/TO/dragonfly-examples/feast-recommendation-duckdb-dragonfly
```

- Install dependencies by using `uv sync` (which also automatically creates a `venv`):

```bash
$> uv sync
```

- From here on, we always use `uv` to run commands, which ensures that the correct Python version and dependencies are used.
- Generate sample data for the recommendation system:

```bash
# Create the 'data' directory to store the Feast registry file and the offline store (DuckDB) database files.
$> mkdir data

# Run the data generation script to create sample Parquet files representing users, items, and interactions.
$> uv run recommendation_01_data.py
```

- Register the Feast objects (entities, feature views, data sources):

```bash
# The 'feast apply' command scans Python files in the current directory for Feast object definitions,
# such as feature views, entities, and data sources. It validates these definitions and then registers them
# by syncing the metadata to the Feast registry. The registry is typically a protobuf binary file stored locally
# or in an object store. As configured in the 'feature_store.yaml', our registry will reside in 'data/registry.db'.
$> uv run feast apply
```

- Loads feature values from offline batch data source (DuckDB) into the online feature store (Dragonfly):

```bash
# The 'feast materialize' command loads feature values from offline batch data sources into
# the online feature store over a specified historical time range. It queries the batch sources
# for all relevant feature views during the given time range and writes the latest feature values into
# the configured online store to make them available for low-latency serving during inference.
$> uv run feast materialize '2024-08-01T00:00:00' '2025-08-31T23:59:59'
```

- Retrieve feature values from the offline store (DuckDB) example:

```bash
$> uv run recommendation_03_historical_features.py
```

- Retrieve feature values from the online store (Dragonfly) example:

```bash
$> uv run recommendation_04_online_features.py
```

- Run the Feast server to serve features via HTTP:

```bash
$> uv run feast serve
```

- Query the Feast server for online features example:

```bash
$> curl --request POST \
  --url http://localhost:6566/get-online-features \
  --header 'Content-Type: application/json' \
  --data '{
	"features": [
		"user_features:age",
		"user_features:gender",
		"user_features:avg_rating",
		"user_features:preferred_category",
		"item_features:category",
		"item_features:price",
		"item_features:popularity_score",
		"item_features:avg_rating",
		"interaction_features:view_count",
		"interaction_features:last_rating",
		"interaction_features:time_since_last_interaction"
	],
	"entities": {
		"user_id": [1, 2],
		"item_id": [101, 102]
	},
	"full_feature_names": true
}'
```

- Build and run the Feast server as a Docker image:

```bash
$> docker build -t my-feast-server .
$> docker run -p 6566:6566 my-feast-server
```

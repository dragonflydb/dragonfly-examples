# Example: Cache Refresh-Ahead

Refresh-Ahead is a strategy that takes a proactive approach by refreshing the cache before the cached key expires, keeping data hot until it's no longer in high demand.

- Start by choosing a refresh-ahead factor, which determines the time before the cached key expires when the cache should be refreshed.
- For example, if your cached data has a lifetime of 100 seconds, and you choose a refresh-ahead factor of 50%:
  - If the data is queried before the 50th second, the cached data will be returned as usual.
  - If the data is queried after the 50th second, the cached data will still be returned, but a background worker will trigger the data refresh.
- It's important to ensure that only one background worker is responsible for refreshing the data to avoid redundant reads to the database.

## Packages Used

- The [Fiber](https://docs.gofiber.io/) web framework is used in this example, as the route handlers are much easier to write than the standard library.
- The [go-redis](https://github.com/redis/go-redis) client is used. It has strongly typed methods for various commands.
  It is also the recommended Go client to interact with Dragonfly.

## Local Setup

- Make sure that you have [Go v1.20+](https://go.dev/dl/) installed locally.
- Make sure that you have [Docker](https://docs.docker.com/engine/install/) installed locally.

## Run Dragonfly & Service Application

- Run a Dragonfly instance with `docker compose` using configurations in the `docker-compose.yml` file:

```bash
# within the root directory of this example (dragonfly-examples/cache-refresh-ahead)
docker compose up -d --remove-orphans cache-refresh-ahead-dragonfly
```

- Install dependencies and run the service application:

```bash
go mod vender

# within the root directory of this example (dragonfly-examples/cache-refresh-ahead)
cd app && go run .
```

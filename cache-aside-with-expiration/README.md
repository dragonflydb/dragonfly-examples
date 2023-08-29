# Example: Cache-Aside

Cache-Aside (or Lazy-Loading) is the most common caching pattern available.
The fundamental data retrieval logic can be summarized as:

- When a service needs a specific piece of data, it queries the cache first.
- Ideally, the required data is readily available in the cache, which is often referred to as a **cache hit**.
- If data is absent from the cache (aptly termed a **cache miss**), the service redirects the query to the primary database instead.
- The cache is also populated with the data retrieved from the database.

## Packages Used

- The [Fiber](https://docs.gofiber.io/) web framework is used in this example, as the route handlers are much easier to write than the standard library.
- The [Fiber cache middleware](https://docs.gofiber.io/api/middleware/cache) is used to demonstrate the Cache-Aside pattern.
- The [go-redis](https://github.com/redis/go-redis) client is used. It has strongly typed methods for various commands.
  It is also the recommended Go client to interact with Dragonfly.

## Local Setup

- Make sure that you have [Go v1.20+](https://go.dev/dl/) installed locally.
- Make sure that you have [Docker](https://docs.docker.com/engine/install/) installed locally.

## Run Dragonfly & Service Application

- Run a Dragonfly instance with `docker compose` using configurations in the `docker-compose.yml` file:

```bash
# within the root directory of this example (dragonfly-examples/cache-aside-with-expiration)
docker compose up -d --remove-orphans cache-aside-dragonfly
```

- Install dependencies and run the service application:

```bash
go mod vender

# within the root directory of this example (dragonfly-examples/cache-aside-with-expiration)
cd app && go run .
```

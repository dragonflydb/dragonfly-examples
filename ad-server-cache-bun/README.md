# Example: Ad Server using Bun, ElysiaJS, and Dragonfly

In this example, we will build a real-time ad server API using Bun, ElysiaJS, and Dragonfly.
In terms of data types, we use `Hash` to store ad metadata and `Set` to store ad categories and user preferences.

## Packages Used

- [ElysiaJS](https://elysiajs.com/) is a TypeScript framework supercharged by the [Bun](https://bun.sh/) runtime with end-to-end type safety.
- [ioredis](https://github.com/redis/ioredis) is a Redis client for Node.js that can be used to interact with Dragonfly.
- [typebox](https://github.com/sinclairzx81/typebox) is a JSON schema type builder and validator with static type resolution for TypeScript.

## Local Setup

- Make sure that you have [Bun v1.0.6+](https://bun.sh/) installed locally.
- Make sure that you have [Docker](https://docs.docker.com/engine/install/) installed locally.

## Run Dragonfly & Service Application

- Run a Dragonfly instance using Docker:

```bash
docker run -p 6379:6379 --ulimit memlock=-1 docker.dragonflydb.io/dragonflydb/dragonfly
```

- Install dependencies and run the service application:

```bash
# within the root directory of this example (dragonfly-examples/ad-server-cache-bun)
bun install
bun run dev # (or `bun dev`)
```

- The ad server API would be running on `http://localhost:3000/`

## Interact with the Ad Server API

- Create ad metadata with the following request:

```shell
curl --request POST \
  --url http://localhost:3888/ads \
  --header 'Content-Type: application/json' \
  --data '{
	"id": "1",
	"title": "Dragonfly - a data store built for modern workloads",
	"category": "technology",
	"clickURL": "https://www.dragonflydb.io/",
	"imageURL": "https://www.dragonflydb.io/blog"
}'
```

- Create or update user preferences with the following request:

```shell
curl --request POST \
  --url http://localhost:3888/ads/user_preferences \
  --header 'Content-Type: application/json' \
  --data '{
	"userId": "1",
	"categories": ["technology", "sports"]
}'
```

- Retrieve ads for a specific user with the following request:

```shell
curl --request GET \
  --url http://localhost:3888/ads/user_preferences/1
```

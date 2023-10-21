# Example: Ad Server using Bun, ElysiaJS, and Dragonfly

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

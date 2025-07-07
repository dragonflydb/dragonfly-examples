# Caching with Dragonfly in 5 Minutes (JavaScript/TypeScript)

Learn how to build a URL-shortener backend (with PostgreSQL for storage and Dragonfly for caching) locally in under 5 minutes!

## Prerequisites

In this example, we use the Bun toolchain to run our TypeScript code. [Bun](https://github.com/oven-sh/bun) is an all-in-one TypeScript/JavaScript runtime & toolkit designed for speed, complete with a bundler, test runner, and Node.js-compatible package manager.

We also use [Docker](https://github.com/docker), which is a platform used to develop, ship, and run applications inside containers. A container is a lightweight, standalone executable that includes everything needed to run a piece of software—code, runtime, system tools, libraries, and settings.

Last but not least, we also use [`npx`](https://docs.npmjs.com/cli/v8/commands/npx) to make the database migration process easier, since it is used by the DrizzleORM kit. However, if you want to skip `npx`, you can find the migration script ending with the `.sql` extension within this repository and apply it to your local database directly as well.

Make sure the prerequisites above are installed before moving forward.

- [Install Bun](https://bun.sh/): 1.2.17+
- [Install Docker Engine](https://docs.docker.com/engine/install/): Client 27.4.0+, Docker Desktop 4.37.2+
- [Install `npx`](https://docs.npmjs.com/cli/v8/commands/npx): 11.0.0+

---

## How to Run

Note that all commands listed below should be run within the current example project's directory: `dragonfly-examples/cache-in-5mins-hono`, instead of the root directory of `dragonfly-examples`.

To install dependencies:

```sh
bun install

#=> bun install v1.2.17 (282dda62)
#=> + @types/bun@1.2.17
#=> + @types/pg@8.15.4
#=> + @hono/zod-validator@0.7.0
#=> + drizzle@1.4.0
#=> + drizzle-kit@0.31.4
#=> + drizzle-orm@0.44.2
#=> + drizzle-zod@0.8.2
#=> + hono@4.8.3
#=> + ioredis@5.6.1
#=> + pg@8.16.3
#=> + uuid@11.1.0
#=> + zod@3.25.74
```

To set up the environment locally (for Dragonfly/Redis and PostgreSQL):

```sh
docker compose up -d

#=> [+] Running 4/4
#=>  ✔ Network cache-in-5mins-hono_default  Created     0.0s
#=>  ✔ Container cache-with-hono-redis      Started     0.2s
#=>  ✔ Container cache-with-hono-dragonfly  Started     0.2s
#=>  ✔ Container cache-with-hono-postgres   Started     0.2s
```

To run the migrations targeting the local PostgreSQL database:

```sh
npx drizzle-kit migrate

#=> No config path provided, using default 'drizzle.config.ts'
#=> Reading config file '/cache-in-5mins-hono/drizzle.config.ts'
#=> Using 'pg' driver for database querying
```

To run the server:

```sh
bun run dev

#=> $ bun run --hot src/index.ts
#=> Started development server: http://localhost:3000
```

---

## Test the API

To create a new short link:

```sh
curl --request POST \
  --url http://localhost:3000/short-links \
  --header 'Content-Type: application/json' \
  --data '{
	"originalUrl": "https://www.google.com/"
}'
```

To test page redirect, use a URL with the returned short code:

```sh
localhost:3000/AZfjZEnZd82iKkXXXXXXXX
```

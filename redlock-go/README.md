# Example: Redlock with Go

[Redlock](https://redis.io/docs/manual/patterns/distributed-locks/) is a recognized algorithm based on Redis for
distributed locks, ensuring consistent operation and protection against failures such as network partitions and Redis crashes.
It operates by having a client application send lock requests, using [`SET`](https://www.dragonflydb.io/docs/command-reference/strings/set.md) commands, to **multiple primary Redis instances**.
The lock is successfully acquired when more than half of these instances agree on the lock acquisition.
To release the lock, the client application uses a Lua script, which involves the [`GET`](https://www.dragonflydb.io/docs/command-reference/strings/get.md) command
and the [`DEL`](https://www.dragonflydb.io/docs/command-reference/generic/del.md) command, to perform compare-and-delete operations on all the instances involved.
Redlock also takes into account the lock validity time, retry on failure, lock extension, and many other aspects, which makes it a robust and reliable solution for distributed locking.

Since Dragonfly is highly compatible with Redis, Redlock implementations can be easily used with Dragonfly.

## Packages Used

- The [go-redis](https://github.com/redis/go-redis) client is used. It has strongly typed methods for various commands.
  It is also the recommended Go client to interact with Dragonfly.
- The [redsync](https://github.com/go-redsync/redsync) is a Go implementation of the Redlock algorithm.
  It is used to acquire and release locks in a distributed environment.

## Local Setup

- Make sure that you have [Go v1.20+](https://go.dev/dl/) installed locally.
- Make sure that you have [Docker](https://docs.docker.com/engine/install/) installed locally.
- Run Dragonfly instances & the Redlock service:

```bash
# within the root directory of this example (dragonfly-examples/redlock-go)
docker compose build --no-cache && docker compose up
```

- Use the API endpoint to acquire the lock:

```bash
curl -v --url http://localhost:8080/try-to-acquire-global-lock
```

- For the first time, the lock should be acquired successfully:

```text
HTTP/1.1 200 OK
Date: Thu, 15 Feb 2024 19:29:09 GMT
Content-Length: 13
Content-Type: text/plain; charset=utf-8

lock acquired
```

- If we try to acquire the lock again in a short period, it should fail:

```text
HTTP/1.1 400 Bad Request
Content-Type: text/plain; charset=utf-8
X-Content-Type-Options: nosniff
Date: Thu, 15 Feb 2024 19:29:56 GMT
Content-Length: 42

lock already taken, locked nodes: [0 1 2]
```

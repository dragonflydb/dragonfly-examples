# Example: Leaderboard

This example demonstrates how to use Dragonfly as an in-memory store to build a real-time leaderboard application.

- We use the `Sorted-Set` data type to store user scores & IDs:

```bash
dragonfly:6380$> ZREVRANGE leaderboard:user_scores 0 10 WITHSCORES
1) "leaderboard:users:1"
2) "500"
3) "leaderboard:users:2"
4) "400"
5) "leaderboard:users:3"
6) "300"
7) "leaderboard:users:4"
8) "200"
```

- We use the `Hash` data type to store user details based on IDs:

```bash
dragonfly:6380$> HGETALL leaderboard:users:1
1) "id"
2) "1"
3) "email"
4) "joe@dragonflydb.io"
5) "nick_name"
6) "Joe"
7) "image_url"
8) "joe_avatar.png"
```

## Packages Used

- The [go-redis](https://github.com/redis/go-redis) client is used. It has strongly typed methods for various commands.
  It is also the recommended Go client to interact with Dragonfly.

## Local Setup

- Make sure that you have [Go v1.20+](https://go.dev/dl/) installed locally.
- Make sure that you have [Docker](https://docs.docker.com/engine/install/) installed locally.

## Leaderboard Application & Migration

- Run in-memory store instances and the leaderboard application service with `docker compose` using configurations in the `docker-compose.yml` file:

```bash
# within the root directory of this example (dragonfly-examples/leaderboard)
docker compose build --no-cache && docker compose up
```

- At this point, the Redis instance (primary) is running on port `6379`.
  The Dragonfly instance (replica) is running on port `6380`.
- The primary-replica topology is monitored and managed by a Sentinel cluster of 3 nodes.
- Now, issue the following command to the Redis instance, and the Sentinel cluster will promote Dragonfly as the primary instance:

```bash
redis:6379$> SHUTDOWN
```

- Alternatively, we can directly instruct the Sentinel cluster to promote Dragonfly as the primary instance:

```bash
sentinel:5001$> SENTINEL FAILOVER leaderboard-primary
OK
```
# Live Migration to Dragonfly Cloud

This repo shows a sample python application that acts like a real-time client to a
Redis-compatible database.

This is used to test and showcase live migration of Redis data to Dragonfly Cloud using
[RedisShake](https://github.com/tair-opensource/RedisShake). With Live Migrations, There is no downtime and the application can continue to read and write to the database without any
interruption.

## How to run

1. Clone the repository

```bash
git clone https://github.com/dragonflydb/live-migration-demo.git
```

2. Install the dependencies

```bash
pip install -r requirements.txt
```

3. Run the application

```bash
python redis_migration_demo.py
```

## How to test live migration

1. Create a new database in Dragonfly Cloud

2. Once the data is inserted, Start running RedisShake to migrate the data to the new database

```bash
docker docker run -v "$(pwd)/redis-shake.toml:/redis-shake-config.toml" \
--entrypoint ./redis-shake \
ghcr.io/tair-opensource/redisshake:latest \
/redis-shake-config.toml
```

3. Once the main sync is done, and keyspace notification sync is taking place, you can switch the application *live* to the new database by

```bash
curl -X POST \
     -H "Content-Type: application/json" \
     -d '{"host": "<datastore_id>.dragonflydb.cloud", "port": 6385, "password": "<password>"}' \
     http://127.0.0.1:8080/update_redis
```

4. As you can see, Even after the migration, the application is still able to read and write to the database without any interruption and no
key loss.
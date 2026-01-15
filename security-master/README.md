## Security Master with Dragonfly

A security master is a centralized repository for all financial instrument data that serves as
the golden source of truth, widely developed and used within financial institutions.

This project contains code for the blog post
[Scaling Real-Time Financial Data Infrastructure: A Modern Security Master Blueprint](https://www.dragonflydb.io/blog/scaling-real-time-financial-data-infrastructure-security-master).

If you want to follow along, make sure **all commands are executed within this project's subdirectory**
(`dragonfly-examples/security-master`).

## How to Run

- First of all, let's make sure a Dragonfly server instance
  is [running locally](https://www.dragonflydb.io/docs/getting-started)
  or [in the cloud](https://www.dragonflydb.io/docs/cloud/getting-started).
- Once you have a Dragonfly server instance running, you can use an environment variable to connect.
  See more details in the `dragonfly.py` file.
- Next, let's use [`uv`](https://github.com/astral-sh/uv) as our Python package and project manager.

```bash
# Install uv with curl:
$> curl -LsSf https://astral.sh/uv/install.sh | sh

# Install uv with wget:
$> wget -qO- https://astral.sh/uv/install.sh | sh
```

- Install dependencies by using `uv sync` (which also automatically creates a `venv`):

```bash
$> uv sync
```

- From here on, we always use `uv` to run commands,
  which ensures that the correct Python version and dependencies are used.
- Get an impression of what a security data model looks like:

```bash
$> uv run model.py
```

- Similarly, you can get a randomly generated security record by running:

```bash
$> uv run generator.py
```

- To load Dragonfly with security data:

```bash
$> uv run loader.py
```

- After loading the data, you can use different JSON and Search commands to query Dragonfly:

```bash
# Sample a few security records.
dragonfly$> SCAN 0 MATCH sec:* COUNT 10

# Details of a security record. (You can replace the key with one returned from the SCAN command.)
dragonfly$> JSON.GET sec:1NVJV44U3PDIHNLP

# Exact match on tag fields.
dragonfly$> FT.SEARCH idx:securities "@sector:{Technology} @exchange:{NASDAQ} @dividend_yield:[0.004 +inf]" SORTBY dividend_yield DESC LIMIT 0 10

# Textual search on security name.
dragonfly$> FT.SEARCH idx:securities "@security_name:*Miller*" RETURN 2 '$.ticker' '$.security_description' LIMIT 0 10
```

- You can also run the `search.py` file for vector search:

```bash
$> uv run search.py
```

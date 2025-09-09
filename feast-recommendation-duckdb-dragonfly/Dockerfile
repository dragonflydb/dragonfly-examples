FROM python:3.11.9-slim AS base

## Builder Stage ##
FROM base AS builder

# Install uv, the Python package manager that actually works.
COPY --from=ghcr.io/astral-sh/uv:0.8.12 /uv /bin/uv
WORKDIR /app

# Copy uv files for better cache.
COPY uv.lock pyproject.toml /app/

# Install dependencies using uv.
RUN uv sync --frozen --no-dev

# Copy the rest of the application code (necessary files only) to run the Feast server.
# Note that we use 'feature_store_docker.yaml' to allow the container to talk to the Dragonfly
# server running on port 6379 within Docker on the host machine.
RUN mkdir -p /app/data
COPY data/registry.db /app/data/registry.db
COPY feature_store_docker.yaml /app/feature_store.yaml
COPY recommendation_02_repo.py recommendation_05_service.py /app/

## Runtime Stage ##
FROM base
COPY --from=builder /app /app
WORKDIR /app

# Activate the virtual environment created by uv.
ENV PATH="/app/.venv/bin:$PATH"

# Run the Feast server.
CMD ["feast", "serve", "--host", "0.0.0.0", "--port", "6566"]

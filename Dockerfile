FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

# Install system dependencies and clean up
RUN apt-get update && apt-get -y install python3-dev libpq-dev && rm -rf /var/lib/apt/lists/*

# Set working directory and PYTHONPATH
WORKDIR /app_root
ENV PYTHONPATH=/app_root

# Copy dependency files and entrypoint
COPY pyproject.toml uv.lock entrypoint.sh ./
RUN chmod +x entrypoint.sh

# Install dependencies
RUN uv venv && uv sync

# Copy application files
COPY alembic alembic/
COPY app app/
COPY alembic.ini .

# Set entrypoint
ENTRYPOINT ["./entrypoint.sh"]

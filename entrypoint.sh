#!/bin/bash
set -e

uv run alembic upgrade head

uv run app/main.py
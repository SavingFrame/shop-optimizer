#!/usr/bin/env bash

set -e
set -x

uv run ty check --exclude 'app/alembic/**' app
ruff check app
ruff format app --check

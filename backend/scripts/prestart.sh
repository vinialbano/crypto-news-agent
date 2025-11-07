#! /usr/bin/env bash

set -e
set -x

# Let the DB start and check Ollama connectivity
python app/scripts/backend_pre_start.py

# Run migrations
alembic upgrade head

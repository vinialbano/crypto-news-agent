#! /usr/bin/env bash

set -e
set -x

# Let the DB start
python app/backend_pre_start.py

# Check Ollama connectivity (3 retries with 5s timeout each)
echo "Checking Ollama connectivity..."
python app/check_ollama.py

# Run migrations
alembic upgrade head

# Create initial data in DB
python app/initial_data.py

# Seed news sources
python -m app.scripts.seed_sources

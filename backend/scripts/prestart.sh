#! /usr/bin/env bash

set -e
set -x

# Let the DB start
python app/backend_pre_start.py

# Check Ollama connectivity
echo "Checking Ollama connectivity..."
python -m app.shared.check_ollama

# Run migrations
alembic upgrade head

# Seed news sources
python -m app.features.news.scripts.seed_sources

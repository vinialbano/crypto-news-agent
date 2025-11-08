#!/bin/bash

# Script to pull required Ollama models
# This should be run after Ollama container starts

set -e

echo "Waiting for Ollama to be ready..."
until curl -s http://ollama:11434/api/tags > /dev/null 2>&1; do
    sleep 2
done

echo "Ollama is ready. Pulling models..."

# Pull embedding model
echo "Pulling nomic-embed-text..."
docker compose exec ollama ollama pull nomic-embed-text

# Pull chat model
echo "Pulling llama3.2:3b..."
docker compose exec ollama ollama pull llama3.2:3b

echo "All models pulled successfully!"

#!/bin/bash

# Script to initialize Ollama with required models
# This runs inside a temporary container that pulls the models

set -e

echo "Waiting for Ollama server to be ready..."
until curl -s http://ollama:11434/api/tags > /dev/null 2>&1; do
    echo "Waiting for Ollama..."
    sleep 2
done

echo "Ollama is ready!"

# Check if models are already installed
echo "Checking installed models..."
MODELS=$(curl -s http://ollama:11434/api/tags | grep -o '"name":"[^"]*"' | cut -d'"' -f4 || echo "")

# Pull embedding model if not installed
if echo "$MODELS" | grep -q "nomic-embed-text"; then
    echo "nomic-embed-text is already installed"
else
    echo "Pulling nomic-embed-text..."
    ollama pull nomic-embed-text
fi

# Pull chat model if not installed (1B Q4_K_M variant for better speed)
if echo "$MODELS" | grep -q "llama3.2:1b-instruct-q4_K_M"; then
    echo "llama3.2:1b-instruct-q4_K_M is already installed"
else
    echo "Pulling llama3.2:1b-instruct-q4_K_M..."
    ollama pull llama3.2:1b-instruct-q4_K_M
fi

echo "All required models are installed!"

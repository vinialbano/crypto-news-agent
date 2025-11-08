#!/bin/bash

# Start Ollama in the background.
/bin/ollama serve &
# Record Process ID.
pid=$!

# Pause for Ollama to start.
sleep 5

echo "🔴 Retrieve nomic-embed-text model..."
ollama pull nomic-embed-text
echo "🟢 Done!"

echo "🔴 Retrieve llama3.2:1b-instruct-q4_K_M model..."
ollama pull llama3.2:1b-instruct-q4_K_M
echo "🟢 Done!"

# Wait for Ollama process to finish.
wait $pid
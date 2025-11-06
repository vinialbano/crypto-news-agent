#!/usr/bin/env bash
# Run only unit tests (fast, no external dependencies)

set -e

cd "$(dirname "$0")/.."

echo "================================================================================"
echo "Running Unit Tests"
echo "================================================================================"
echo

# Set TEST_MODE to use .env.test for local testing
export TEST_MODE=1

uv run pytest tests/unit/ -v "$@"

echo
echo "✅ Unit tests completed!"

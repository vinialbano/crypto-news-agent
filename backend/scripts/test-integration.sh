#!/usr/bin/env bash
# Run integration tests (requires Docker services)

set -e

cd "$(dirname "$0")/.."

echo "================================================================================"
echo "Running Integration Tests"
echo "================================================================================"
echo

# Set TEST_MODE to use .env.test for local testing
export TEST_MODE=1

uv run pytest tests/integration/ -m integration -v "$@"

echo
echo "✅ Integration tests completed!"

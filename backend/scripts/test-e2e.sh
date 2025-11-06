#!/usr/bin/env bash
# Run end-to-end tests (requires Docker services and data)

set -e

cd "$(dirname "$0")/.."

echo "================================================================================"
echo "Running End-to-End Tests"
echo "================================================================================"
echo

# Set TEST_MODE to use .env.test for local testing
export TEST_MODE=1

uv run pytest tests/e2e/ -m e2e -v "$@"

echo
echo "✅ End-to-end tests completed!"

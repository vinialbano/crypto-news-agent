#!/usr/bin/env bash
# Run all tests with coverage

set -e

cd "$(dirname "$0")/.."

echo "================================================================================"
echo "Running Complete Test Suite"
echo "================================================================================"
echo

# Set TEST_MODE to use .env.test for local testing
export TEST_MODE=1

# Run tests with coverage
echo "Running tests..."
uv run pytest \
    --cov=app \
    --cov-report=term-missing \
    --cov-report=html \
    "$@"

echo
echo "================================================================================"
echo "✅ All tests completed!"
echo "================================================================================"
echo
echo "Coverage report generated: htmlcov/index.html"

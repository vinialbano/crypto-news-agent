#! /usr/bin/env bash

set -e
set -x

# Run database migrations
alembic upgrade head

"""Test configuration and fixtures."""

import asyncio
from collections.abc import Generator

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session

from app.core.db import engine
from app.main import app


@pytest.fixture(scope="session")
def event_loop():
    """Create an event loop for the entire test session.

    This prevents 'Event loop is closed' errors when running async operations
    in sync tests (like WebSocket tests with async embeddings).
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session", autouse=True)
def db() -> Generator[Session, None, None]:
    """Initialize database for tests.

    Database schema is created with Alembic migrations.
    """
    with Session(engine) as session:
        yield session
        # Cleanup handled by test database


@pytest.fixture(scope="module")
def client() -> Generator[TestClient, None, None]:
    """Create test client."""
    with TestClient(app) as c:
        yield c

"""Shared pytest fixtures."""

import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.storage import repository


@pytest.fixture
def client() -> TestClient:
    """Provide a test client and reset in-memory storage around each test."""
    repository.clear()
    with TestClient(app) as test_client:
        yield test_client
    repository.clear()

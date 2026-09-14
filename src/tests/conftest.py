import pytest
from fastapi.testclient import TestClient

from src.app import app
from src.storage import repository


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_repository():
    """每个用例前后清空内存存储，保证隔离。"""
    repository.clear()          # 若你的 repository 没有 clear，见下方说明
    yield
    repository.clear()
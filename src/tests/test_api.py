"""API and repository tests covering the required CRUD paths."""

from fastapi.testclient import TestClient

from src.models.task import TaskCreate, TaskStatus, TaskUpdate
from src.storage import InMemoryTaskRepository, repository


def _create_task(client: TestClient, title: str = "Write docs") -> dict:
    response = client.post(
        "/tasks",
        json={"title": title, "description": "Draft the README", "status": "todo"},
    )
    assert response.status_code == 201
    return response.json()


def test_health_returns_ok(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_list_tasks_initially_empty(client: TestClient) -> None:
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_create_and_get_task(client: TestClient) -> None:
    created = _create_task(client)
    assert created["title"] == "Write docs"
    assert created["status"] == "todo"
    assert created["id"]
    assert created["created_at"].endswith("Z")
    assert created["updated_at"].endswith("Z")

    response = client.get(f"/tasks/{created['id']}")
    assert response.status_code == 200
    assert response.json()["id"] == created["id"]


def test_create_task_rejects_blank_title(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": "   "})
    assert response.status_code == 400
    body = response.json()
    assert body["detail"] == "Invalid request body"


def test_create_task_rejects_invalid_status(client: TestClient) -> None:
    response = client.post("/tasks", json={"title": "Bad status", "status": "archived"})
    assert response.status_code == 400


def test_get_missing_task_returns_404(client: TestClient) -> None:
    response = client.get("/tasks/missing-id")
    assert response.status_code == 404
    assert response.json()["detail"] == "Task not found"


def test_update_task(client: TestClient) -> None:
    created = _create_task(client)
    response = client.put(
        f"/tasks/{created['id']}",
        json={"title": "Write API docs", "status": "in_progress"},
    )
    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "Write API docs"
    assert body["status"] == "in_progress"
    assert body["description"] == "Draft the README"


def test_update_task_rejects_blank_title(client: TestClient) -> None:
    created = _create_task(client)
    response = client.put(f"/tasks/{created['id']}", json={"title": "   "})
    assert response.status_code == 400


def test_update_missing_task_returns_404(client: TestClient) -> None:
    response = client.put("/tasks/missing-id", json={"title": "Nope"})
    assert response.status_code == 404


def test_delete_task(client: TestClient) -> None:
    created = _create_task(client, title="Temp task")
    response = client.delete(f"/tasks/{created['id']}")
    assert response.status_code == 204
    assert client.get(f"/tasks/{created['id']}").status_code == 404


def test_delete_missing_task_returns_404(client: TestClient) -> None:
    response = client.delete("/tasks/missing-id")
    assert response.status_code == 404


def test_openapi_docs_available(client: TestClient) -> None:
    docs = client.get("/docs")
    openapi = client.get("/openapi.json")
    assert docs.status_code == 200
    assert openapi.status_code == 200
    assert openapi.json()["info"]["title"] == "Task Manager API"


def test_in_memory_repository_crud() -> None:
    store = InMemoryTaskRepository()
    created = store.create_task(TaskCreate(title="Repo test", description="unit"))
    assert store.get_task(created.id) is not None
    assert len(store.list_tasks()) == 1

    updated = store.update_task(created.id, TaskUpdate(status=TaskStatus.DONE))
    assert updated is not None
    assert updated.status == TaskStatus.DONE

    assert store.delete_task(created.id) is True
    assert store.get_task(created.id) is None
    assert store.update_task(created.id, TaskUpdate(title="gone")) is None
    assert store.delete_task(created.id) is False


def test_update_task_keeps_title_when_omitted(client: TestClient) -> None:
    created = _create_task(client)
    response = client.put(f"/tasks/{created['id']}", json={"description": "updated only"})
    assert response.status_code == 200
    assert response.json()["title"] == created["title"]
    assert response.json()["description"] == "updated only"


def test_shared_repository_can_be_cleared() -> None:
    repository.create_task(TaskCreate(title="leftover"))
    repository.clear()
    assert repository.list_tasks() == []


def test_config_defaults(monkeypatch) -> None:
    monkeypatch.delenv("PORT", raising=False)
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    monkeypatch.delenv("RATE_LIMIT", raising=False)
    from src.config import get_log_level, get_port, get_rate_limit

    assert get_port() == 8080
    assert get_log_level() == "INFO"
    assert get_rate_limit() == "60/minute"

import pytest


# ---------- GET /tasks ----------

def test_list_tasks_empty(client):
    resp = client.get("/tasks")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_tasks_returns_all(client):
    client.post("/tasks", json={"title": "A"})
    client.post("/tasks", json={"title": "B"})

    resp = client.get("/tasks")
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    assert {t["title"] for t in data} == {"A", "B"}


# ---------- GET /tasks/{id} ----------

def test_get_task_ok(client):
    created = client.post("/tasks", json={"title": "读一个"}).json()
    task_id = created["id"]

    resp = client.get(f"/tasks/{task_id}")
    assert resp.status_code == 200
    assert resp.json()["id"] == task_id
    assert resp.json()["title"] == "读一个"


def test_get_task_not_found(client):
    resp = client.get("/tasks/does-not-exist")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Task not found"


# ---------- POST /tasks ----------

def test_create_task_ok(client):
    payload = {"title": "写测试", "description": "给接口补测试"}
    resp = client.post("/tasks", json=payload)

    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == payload["title"]
    assert data["description"] == payload["description"]
    assert "id" in data
    # 默认 status
    assert data.get("status") == "todo"


def test_create_task_missing_title(client):
    """缺 title → 你的全局异常处理返回 400"""
    resp = client.post("/tasks", json={"description": "没有标题"})
    assert resp.status_code == 400


def test_create_task_empty_title(client):
    """空标题 → 400"""
    resp = client.post("/tasks", json={"title": ""})
    assert resp.status_code == 400


def test_create_task_invalid_status(client):
    """非法 status 值 → 400"""
    resp = client.post("/tasks", json={"title": "x", "status": "not-a-status"})
    assert resp.status_code == 400


def test_create_task_invalid_json(client):
    """非法 JSON body → 400"""
    resp = client.post(
        "/tasks",
        content="{not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 400


# ---------- PUT /tasks/{id} ----------

def test_update_task_ok(client):
    created = client.post("/tasks", json={"title": "旧标题"}).json()
    task_id = created["id"]

    resp = client.put(f"/tasks/{task_id}", json={"title": "新标题"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "新标题"
    assert resp.json()["id"] == task_id


def test_update_task_partial(client):
    """只改 status，title 应保留"""
    created = client.post("/tasks", json={"title": "保留", "status": "todo"}).json()
    task_id = created["id"]

    resp = client.put(f"/tasks/{task_id}", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "保留"
    assert resp.json()["status"] == "done"


def test_update_task_not_found(client):
    resp = client.put("/tasks/nope", json={"title": "x"})
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Task not found"


def test_update_task_invalid_status(client):
    created = client.post("/tasks", json={"title": "x"}).json()
    resp = client.put(f"/tasks/{created['id']}", json={"status": "bad"})
    assert resp.status_code == 400


# ---------- DELETE /tasks/{id} ----------

def test_delete_task_ok(client):
    created = client.post("/tasks", json={"title": "待删除"}).json()
    task_id = created["id"]

    resp = client.delete(f"/tasks/{task_id}")
    assert resp.status_code == 204
    assert resp.content == b""          # 204 必须没有 body

    # 删除后再查 → 404
    assert client.get(f"/tasks/{task_id}").status_code == 404


def test_delete_task_not_found(client):
    resp = client.delete("/tasks/nope")
    assert resp.status_code == 404
    assert resp.json()["detail"] == "Task not found"


# ---------- 参数化：批量校验 ----------

@pytest.mark.parametrize("payload", [
    {},                          # 空对象
    {"description": "无标题"},   # 缺 title
    {"title": ""},               # 空 title
    {"title": "x", "status": "unknown"},   # 非法 status
])
def test_create_task_validation_errors(client, payload):
    resp = client.post("/tasks", json=payload)
    assert resp.status_code == 400
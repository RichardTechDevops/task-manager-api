from fastapi.testclient import TestClient
from src.app import app   # 从模块里导入 app 实例

client = TestClient(app)


def test_health():
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
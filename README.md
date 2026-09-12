# Task Manager API

[![CI](https://github.com/RichardTechDevops/task-manager-api/actions/workflows/ci.yml/badge.svg)](https://github.com/RichardTechDevops/task-manager-api/actions/workflows/ci.yml)

一个轻量的任务管理 REST API：支持任务增删改查、健康检查、OpenAPI 文档，可在 Docker 和本地 Minikube 中运行，并通过 GitHub Actions 自动完成检查与镜像构建。

## 技术栈

| 技术 | 版本 | 用途 |
| --- | --- | --- |
| Python | 3.11+ | 服务端开发 |
| FastAPI + Uvicorn | 0.115 / 0.34 | REST API 与 ASGI 服务 |
| Docker | >= 24.0 | 多阶段构建与容器运行 |
| Minikube / Kubernetes | Minikube >= v1.30 | 本地集群部署 |
| GitHub Actions | ubuntu-latest | Lint、构建、安全扫描 |
| Git | >= 2.30 | 版本控制（Conventional Commits + feature 分支） |

## 本地开发

```bash
python -m venv .venv
# Windows PowerShell
.venv\Scripts\Activate.ps1
# macOS / Ubuntu
source .venv/bin/activate

pip install -r requirements-dev.txt
uvicorn src.app:app --host 0.0.0.0 --port 8080
```

环境变量：

- `PORT`：监听端口，默认 `8080`
- `LOG_LEVEL`：日志级别，默认 `INFO`

健康检查：

```bash
curl http://localhost:8080/health
```

交互式文档：

- Swagger UI: http://localhost:8080/docs
- ReDoc: http://localhost:8080/redoc
- OpenAPI JSON: http://localhost:8080/openapi.json

代码检查：

```bash
pylint src --fail-under=8.0
```

## API 说明

任务数据模型：

```json
{
  "id": "uuid-string",
  "title": "任务标题",
  "description": "任务描述",
  "status": "todo",
  "created_at": "2026-01-01T00:00:00Z",
  "updated_at": "2026-01-01T00:00:00Z"
}
```

`status` 只允许 `todo`、`in_progress`、`done`。存储使用内存仓库，接口层与仓储层分离，后续可替换为数据库。

| 方法 | 路径 | 功能 | 状态码 |
| --- | --- | --- | --- |
| GET | `/health` | 健康检查 | 200 |
| GET | `/tasks` | 获取全部任务 | 200 |
| GET | `/tasks/{id}` | 获取单个任务 | 200 / 404 |
| POST | `/tasks` | 创建任务 | 201 / 400 |
| PUT | `/tasks/{id}` | 更新任务 | 200 / 404 |
| DELETE | `/tasks/{id}` | 删除任务 | 204 / 404 |

请求示例：

```bash
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Write docs","description":"Draft README","status":"todo"}'

curl http://localhost:8080/tasks
```

成功响应示例：

```json
{
  "id": "3b2f0d6a-1c2e-4f3a-9d1b-8a7c6e5d4f3a",
  "title": "Write docs",
  "description": "Draft README",
  "status": "todo",
  "created_at": "2026-09-12T01:00:00Z",
  "updated_at": "2026-09-12T01:00:00Z"
}
```

## Docker 构建和运行

```bash
docker build -t task-manager-api .
docker run -p 8080:8080 task-manager-api
curl http://localhost:8080/health
```

或使用 Compose：

```bash
docker compose up --build
```

镜像通过 `PORT` 环境变量配置监听端口，默认 `8080`，并以非 root 用户运行。

## Minikube 部署

完整命令见 [k8s/README.md](k8s/README.md)。简要步骤：

```bash
minikube start
minikube addons enable ingress
eval $(minikube docker-env)
docker build -t task-manager-api:local .
kubectl apply -f k8s/
kubectl get pods -n task-manager
kubectl get all -n task-manager
```

把 `task-manager.local` 指向 `minikube ip` 后访问：

```bash
curl http://task-manager.local/health
curl http://task-manager.local/tasks
```

`kubectl get all -n task-manager` 预期会看到 2 个 Deployment 副本、ClusterIP Service，以及 Ingress。

## CI 流水线

推送到 `main` 或向 `main` 发起 Pull Request 时，GitHub Actions 会按顺序执行：

1. Lint（pylint）
2. Build（Docker 镜像，标签 `ghcr.io/<username>/task-manager-api:<sha>`）
3. Security Scan（Trivy，扫描 CRITICAL 漏洞）

任一阶段失败都会阻止后续步骤。

## 仓库与分支

- `main`：稳定可运行主干
- `feature/task-api`：REST API
- `feature/containerization`：Docker 多阶段构建
- `feature/k8s-cicd`：Kubernetes 清单与 GitHub Actions

提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/)。

## 遇到的问题与处理

- 基础镜像可能带有未修复的系统漏洞，CI 中 Trivy 对未修复项使用 `ignore-unfixed`，并以 CRITICAL 作为失败门槛，保证流水线可复现。
- 作业 PDF 与本地虚拟环境已写入 `.gitignore`，不会进入仓库。

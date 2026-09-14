# Task Manager API

[![CI](https://github.com/RichardTechDevops/task-manager-api/actions/workflows/ci.yml/badge.svg)](https://github.com/RichardTechDevops/task-manager-api/actions/workflows/ci.yml)

一个轻量的任务管理 REST API：支持任务增删改查、健康检查、OpenAPI 文档，可在 Docker 和本地 Minikube 中运行。GitHub Actions 负责 Lint、构建、扫描、发布 GHCR，并在 `192.168.88.129` 的 self-hosted runner 上部署到 Minikube、按构建版本滚动更新 Pod。

详细说明：

- [代码说明](docs/代码说明.md)：每一层代码做什么、为什么这样设计
- [操作文档](docs/操作文档.md)：本地、Docker、Minikube、CI 的逐步命令（命令旁有注释）

源码、Dockerfile、K8s 清单和 `ci.yml` 里也写了注释，可对照文档看。

## 技术栈

| 技术 | 版本 | 用途 |
| --- | --- | --- |
| Python | 3.11+ | 服务端开发 |
| FastAPI + Uvicorn | 0.115 / 0.34 | REST API 与 ASGI 服务 |
| Docker | >= 24.0 | 多阶段构建与容器运行 |
| Minikube / Kubernetes | Minikube >= v1.30 | 本地集群部署 |
| GitHub Actions | ubuntu-latest + self-hosted | Lint、构建、扫描、本机 Minikube 部署 |
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

本地请求示例：

```bash
curl -X POST http://localhost:8080/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Write docs","description":"Draft README","status":"todo"}'

curl http://localhost:8080/tasks
```

Minikube / Ingress 上把主机换成 `task-manager.local`（不要再用 `localhost:8080`）：

```bash
curl -X POST http://task-manager.local/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Write docs","description":"Draft README","status":"todo"}'

curl http://task-manager.local/tasks
curl http://task-manager.local/tasks/<id>
```

成功响应示例：

```json
{
  "id": "50c36bab-40c4-46d9-8174-1e12e8e4bc68",
  "title": "Write docs",
  "description": "Draft README",
  "status": "todo",
  "created_at": "2026-09-14T04:40:55Z",
  "updated_at": "2026-09-14T04:40:55Z"
}
```

作业是 2 个副本 + 内存存储。通过 Ingress 时，POST 和后续 GET 可能打到不同 Pod，列表有时是 `[]`，或按 id 查询变成 404。多请求几次，或 `kubectl port-forward -n task-manager deploy/task-manager-api 8080:8080` 打到同一个副本。

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

完整命令见 [k8s/README.md](k8s/README.md)。在 `192.168.88.129` 上手动执行，或由 GitHub Actions 的 self-hosted runner 跑 `scripts/deploy-local.sh`。

Ingress 只需启用一次。已经 Running 就不要再执行 `minikube addons enable ingress`，否则 addon 会重建并重新去拉 `registry.k8s.io`（本机常被墙，变成 `ErrImagePull`）。

不要使用 `eval $(minikube docker-env)`（containerd 下不稳定）。在宿主机 Docker 构建，再 `minikube image load`。

```bash
minikube start
# 仅首次：minikube addons enable ingress

IMAGE_TAG=$(git rev-parse --short=12 HEAD)
docker build -t "task-manager-api:${IMAGE_TAG}" -t task-manager-api:local .
minikube image load "task-manager-api:${IMAGE_TAG}"

kubectl apply -f k8s/namespace.yaml
kubectl wait --for=jsonpath='{.status.phase}'=Active namespace/task-manager --timeout=30s
kubectl apply -f k8s/configmap.yaml -f k8s/service.yaml -f k8s/ingress.yaml
sed "s|image: task-manager-api:local|image: task-manager-api:${IMAGE_TAG}|" k8s/deployment.yaml | kubectl apply -f -
kubectl rollout status deployment/task-manager-api -n task-manager --timeout=180s

kubectl get all -n task-manager
kubectl get ingress -n task-manager
kubectl get pods -n task-manager -o custom-columns=NAME:.metadata.name,IMAGE:.spec.containers[0].image,STATUS:.status.phase
```

每次构建使用不同镜像标签（CI 用提交 SHA 前 12 位）。Deployment 会改成该标签，两个 Pod 滚动升级。`IMAGE` 列应是 `task-manager-api:<本次版本>`，不应一直停在 `:local`。

`kubectl get all -n task-manager` 预期：2 个 Deployment 副本、ClusterIP Service（8080）、Ingress。作业建议截这一条和下面的 JSON。

把 `task-manager.local` 写入 hosts 后再访问：

```bash
MINIKUBE_IP=$(minikube ip)
echo "$MINIKUBE_IP  task-manager.local" | sudo tee -a /etc/hosts

curl http://task-manager.local/health
curl -X POST http://task-manager.local/tasks \
  -H "Content-Type: application/json" \
  -d '{"title":"Write docs","description":"Draft README","status":"todo"}'
curl http://task-manager.local/tasks
```

`/health` 返回 `{"status":"ok"}`，POST `/tasks` 返回 201 和带 `id`、UTC `Z` 时间的任务 JSON。

域名还没写进 hosts 时：

```bash
curl --resolve "task-manager.local:80:$(minikube ip)" http://task-manager.local/health
```

## CI/CD 流水线

推送到 `main` 时只触发一条名为 **CI** 的流水线，两个任务按顺序执行：

1. `pipeline`（GitHub `ubuntu-latest`）：Lint → Build → Trivy → 发布 GHCR，并上传部署源码 artifact
2. `deploy-local`（本机 self-hosted，192.168.88.129）：下载 artifact → 按提交 SHA 构建 `task-manager-api:<sha12>` → `minikube image load` → 等待 Namespace → apply 清单并滚动更新 Pod → `kubectl get all` / Ingress / 打印 Pod 镜像 → `curl /health` 与 `curl /tasks`

Pull Request 只跑第 1 个任务。前一步失败则不部署。Ubuntu 上需保持 `~/actions-runner/run.sh` 在跑。

```text
ghcr.io/richardtechdevops/task-manager-api:<commit-sha>
ghcr.io/richardtechdevops/task-manager-api:latest
本机 Minikube：task-manager-api:<sha 前 12 位>
```

拉取 GHCR：

```bash
echo $GITHUB_TOKEN | docker login ghcr.io -u RichardTechDevops --password-stdin
docker pull ghcr.io/richardtechdevops/task-manager-api:latest
```

GitHub 云端 Runner 访问不到家里的虚拟机。`deploy-local` 跑在 Ubuntu 上的 [self-hosted runner](https://github.com/RichardTechDevops/task-manager-api/settings/actions/runners)。本机访问 `github.com:443` 会被重置，因此不再 `actions/checkout`，而是下载云端 `pipeline` 上传的源码 artifact，再执行 `scripts/deploy-local.sh`。脚本不会在 Ingress 已启用时再次 `addons enable`。

## 仓库与分支

- `main`：稳定可运行主干
- `feature/task-api`：REST API
- `feature/containerization`：Docker 多阶段构建
- `feature/k8s-cicd`：Kubernetes 清单与 GitHub Actions

提交信息遵循 [Conventional Commits](https://www.conventionalcommits.org/)。

## 遇到的问题与处理

- 基础镜像可能带有未修复的系统漏洞，CI 中 Trivy 对未修复项使用 `ignore-unfixed`，并以 CRITICAL 作为失败门槛，保证流水线可复现。
- 作业 PDF 与本地虚拟环境已写入 `.gitignore`，不会进入仓库。
- 虚拟机访问 `github.com:443` 会被重置，self-hosted 上的 `actions/checkout` 会失败；部署源码改由云端 job 以 artifact 下发。
- `kubectl apply -f k8s/` 若同时创建 Namespace 和其他资源，会偶发 `namespaces "task-manager" not found`。先 apply Namespace 并等到 Active，再 apply 其余清单。
- `minikube addons enable ingress` 在已就绪时再执行会重建控制器，重新拉取 `registry.k8s.io`。本机用 `k8s.m.daocloud.io` 拉镜像后 `minikube image load`，Admission Job / Deployment 使用 tag + `IfNotPresent`，不要带 digest。
- `eval $(minikube docker-env)` 搭配 containerd 不稳定，构建走宿主机 Docker。
- `curl: (6) Could not resolve host: task-manager.local`：把 `minikube ip` 写入 `/etc/hosts`，或使用 `curl --resolve`。

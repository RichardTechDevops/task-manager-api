# Kubernetes 部署说明

在本地 Minikube 上部署 Task Manager API。更完整的步骤见 [docs/操作文档.md](../docs/操作文档.md)。

## 前置条件

- Minikube >= v1.30
- kubectl
- Docker（用来构建本地镜像）

## 部署步骤

```bash
# 启动本地集群
minikube start

# 启用 Ingress，后面才能用域名访问
minikube addons enable ingress

# 让 docker 命令打到 Minikube 内部（Windows PowerShell 用下一行）
eval $(minikube docker-env)
# minikube docker-env | Invoke-Expression

# 构建集群可使用的本地镜像
docker build -t task-manager-api:local .

# 创建全部资源：Namespace / ConfigMap / Deployment / Service / Ingress
kubectl apply -f k8s/

# 确认 2 个 Pod 就绪
kubectl get pods -n task-manager
kubectl wait --for=condition=ready pod -l app=task-manager-api -n task-manager --timeout=120s
```

## 通过 Ingress 访问

```bash
# 查看 Minikube IP，写进本机 hosts
minikube ip
```

hosts 增加一行（Windows：`C:\Windows\System32\drivers\etc\hosts`）：

```
<MINIKUBE_IP> task-manager.local
```

```bash
# 作业要求的验证
curl http://task-manager.local/health
curl http://task-manager.local/tasks
```

## 验证命令

```bash
# 作业建议截图这一条
kubectl get all -n task-manager
kubectl get ingress -n task-manager
kubectl logs -n task-manager -l app=task-manager-api
```

## 清理

```bash
kubectl delete -f k8s/
minikube stop
```

# Kubernetes 部署说明

在本地 Minikube 集群中部署 Task Manager API。

## 前置条件

- Minikube >= v1.30
- kubectl
- Docker（用于构建本地镜像）

## 部署步骤

```bash
minikube start
minikube addons enable ingress
eval $(minikube docker-env)
docker build -t task-manager-api:local .
kubectl apply -f k8s/
kubectl get pods -n task-manager
kubectl wait --for=condition=ready pod -l app=task-manager-api -n task-manager --timeout=120s
```

## 通过 Ingress 访问

把 `task-manager.local` 指向 Minikube IP：

```bash
minikube ip
```

在 `/etc/hosts`（Windows: `C:\Windows\System32\drivers\etc\hosts`）中添加：

```
<MINIKUBE_IP> task-manager.local
```

然后验证：

```bash
curl http://task-manager.local/health
curl http://task-manager.local/tasks
```

## 验证命令

```bash
kubectl get all -n task-manager
kubectl get ingress -n task-manager
kubectl logs -n task-manager -l app=task-manager-api
```

## 清理

```bash
kubectl delete -f k8s/
minikube stop
```

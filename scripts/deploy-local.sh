#!/usr/bin/env bash
# 在本地 Ubuntu / Minikube 上发布：从 GHCR 拉镜像，打成本地标签，滚动重启。
set -euo pipefail

IMAGE="${IMAGE:-ghcr.io/richardtechdevops/task-manager-api:latest}"
LOCAL_TAG="${LOCAL_TAG:-task-manager-api:local}"
NAMESPACE="${NAMESPACE:-task-manager}"

if ! command -v docker >/dev/null; then
  echo "docker 不在 PATH 里"
  exit 1
fi
if ! command -v minikube >/dev/null; then
  echo "minikube 未安装"
  exit 1
fi
if ! command -v kubectl >/dev/null; then
  echo "kubectl 未安装"
  exit 1
fi

minikube status >/dev/null

# 镜像打进 Minikube 使用的 Docker
eval "$(minikube docker-env)"
docker pull "${IMAGE}"
docker tag "${IMAGE}" "${LOCAL_TAG}"

kubectl apply -f k8s/
kubectl -n "${NAMESPACE}" rollout restart deployment/task-manager-api
kubectl -n "${NAMESPACE}" rollout status deployment/task-manager-api --timeout=180s
kubectl -n "${NAMESPACE}" get pods

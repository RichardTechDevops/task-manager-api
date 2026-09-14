#!/usr/bin/env bash
# 在 192.168.88.129 的 self-hosted runner 上执行 README 的 Minikube 部署步骤。
set -euo pipefail

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

if ! minikube status >/dev/null 2>&1; then
  minikube start --driver=docker
fi
minikube addons enable ingress

eval "$(minikube docker-env)"
docker build -t task-manager-api:local .
kubectl apply -f k8s/
kubectl get pods -n task-manager
kubectl get all -n task-manager

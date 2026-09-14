#!/usr/bin/env bash
# 在 192.168.88.129 的 self-hosted runner 上执行 README 的 Minikube 部署与验证。
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

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

load_ingress_images() {
  docker pull k8s.m.daocloud.io/ingress-nginx/controller:v1.15.1
  docker tag k8s.m.daocloud.io/ingress-nginx/controller:v1.15.1 \
    registry.k8s.io/ingress-nginx/controller:v1.15.1
  minikube image load registry.k8s.io/ingress-nginx/controller:v1.15.1

  docker pull k8s.m.daocloud.io/ingress-nginx/kube-webhook-certgen:v1.6.9
  docker tag k8s.m.daocloud.io/ingress-nginx/kube-webhook-certgen:v1.6.9 \
    registry.k8s.io/ingress-nginx/kube-webhook-certgen:v1.6.9
  minikube image load registry.k8s.io/ingress-nginx/kube-webhook-certgen:v1.6.9
}

if ! minikube status >/dev/null 2>&1; then
  minikube start --driver=docker
fi

# 已经启用过就不要再 enable：会重建 addon，重新去拉 registry.k8s.io。
if minikube addons list | grep -E '^[[:space:]]*ingress[[:space:]]' | grep -q enabled; then
  echo "ingress addon already enabled, skip minikube addons enable"
else
  load_ingress_images
  minikube addons enable ingress
fi

# 若 controller 还在拉镜像，补灌本地镜像并改成 IfNotPresent。
if ! kubectl -n ingress-nginx get pods -l app.kubernetes.io/component=controller \
      --no-headers 2>/dev/null | grep -q '1/1'; then
  load_ingress_images
  kubectl -n ingress-nginx set image deploy/ingress-nginx-controller \
    controller=registry.k8s.io/ingress-nginx/controller:v1.15.1 || true
  kubectl -n ingress-nginx patch deploy ingress-nginx-controller --type=json \
    -p '[{"op":"replace","path":"/spec/template/spec/containers/0/imagePullPolicy","value":"IfNotPresent"}]' || true
fi

# 宿主机 Docker 构建后再导入集群，避开 minikube docker-env + containerd 的问题。
if minikube docker-env -u >/dev/null 2>&1; then
  eval "$(minikube docker-env -u)" || true
fi
docker build -t task-manager-api:local .
minikube image load task-manager-api:local

kubectl apply -f k8s/

kubectl wait --namespace ingress-nginx \
  --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=180s

kubectl wait --for=condition=ready pod \
  -l app=task-manager-api \
  -n task-manager \
  --timeout=180s

echo "===== kubectl get all -n task-manager ====="
kubectl get all -n task-manager

echo "===== kubectl get ingress -n task-manager ====="
kubectl get ingress -n task-manager

MINIKUBE_IP="$(minikube ip)"
echo "${MINIKUBE_IP}  task-manager.local"

if sudo -n true 2>/dev/null; then
  if grep -qE '[[:space:]]task-manager\.local([[:space:]]|$)' /etc/hosts; then
    sudo sed -i -E "s/^[0-9a-fA-F.:]+[[:space:]]+task-manager\.local.*/${MINIKUBE_IP} task-manager.local/" /etc/hosts
  else
    echo "${MINIKUBE_IP}  task-manager.local" | sudo tee -a /etc/hosts >/dev/null
  fi
else
  echo "没有免密 sudo，不改 /etc/hosts，改用 curl --resolve"
fi

echo "===== curl http://task-manager.local/health ====="
curl -fsS --retry 12 --retry-delay 5 --retry-all-errors \
  --resolve "task-manager.local:80:${MINIKUBE_IP}" \
  http://task-manager.local/health
echo

echo "===== curl http://task-manager.local/tasks ====="
curl -fsS --retry 12 --retry-delay 5 --retry-all-errors \
  --resolve "task-manager.local:80:${MINIKUBE_IP}" \
  http://task-manager.local/tasks
echo

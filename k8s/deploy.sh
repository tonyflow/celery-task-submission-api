#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "==> Creating kind cluster..."
kind create cluster --name api-playground --config "$SCRIPT_DIR/kind-config.yaml" || echo "Cluster already exists"

echo "==> Building Docker images..."
docker build -t api-playground-api:latest "$PROJECT_DIR/api"
docker build -t api-playground-worker:latest "$PROJECT_DIR/worker"

echo "==> Loading images into kind..."
kind load docker-image api-playground-api:latest --name api-playground
kind load docker-image api-playground-worker:latest --name api-playground

echo "==> Applying Kubernetes manifests..."
kubectl apply -k "$SCRIPT_DIR"

echo "==> Waiting for pods to be ready..."
kubectl wait --for=condition=ready pod -l app=postgres -n api-playground --timeout=120s
kubectl wait --for=condition=ready pod -l app=redis -n api-playground --timeout=60s
kubectl wait --for=condition=ready pod -l app=rabbitmq -n api-playground --timeout=120s

echo "==> Waiting for migrations job..."
kubectl wait --for=condition=complete job/migrations -n api-playground --timeout=120s || true

echo "==> Waiting for web deployment..."
kubectl wait --for=condition=available deployment/web -n api-playground --timeout=120s || true

echo ""
echo "==> Deployment complete!"
echo "API available at: http://localhost:8000"
echo ""
echo "Useful commands:"
echo "  kubectl get pods -n api-playground"
echo "  kubectl logs -f deployment/web -n api-playground"
echo "  kubectl logs -f deployment/worker -n api-playground"
echo ""
echo "To delete the cluster:"
echo "  kind delete cluster --name api-playground"

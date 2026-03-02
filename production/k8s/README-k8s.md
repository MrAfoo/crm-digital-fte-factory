# NovaDeskAI Kubernetes Deployment Guide (Kind)

## Prerequisites

Install these tools:

| Tool | Purpose | Install |
|------|---------|--------|
| Docker Desktop | Container runtime | https://docs.docker.com/get-docker/ |
| Kind | K8s in Docker | `choco install kind` or https://kind.sigs.k8s.io |
| kubectl | K8s CLI | `choco install kubernetes-cli` |

## Quick Start (3 commands)

```powershell
# 1. Deploy everything
.\production\k8s\deploy.ps1

# 2. Check status
kubectl get pods -n novadesk

# 3. Access API
curl http://localhost:30800/health
```

## Architecture on Kubernetes

```
Kind Cluster (novadesk)
├── Namespace: novadesk
│   ├── Deployments
│   │   ├── nova-api (2 replicas, port 8000)
│   │   ├── nova-worker (1 replica)
│   │   ├── postgres (1 replica)
│   │   ├── kafka (1 replica)
│   │   └── zookeeper (1 replica)
│   ├── Services
│   │   ├── nova-api-service (NodePort: 30800)
│   │   ├── postgres-service (ClusterIP: 5432)
│   │   ├── kafka-service (ClusterIP: 9092)
│   │   └── zookeeper-service (ClusterIP: 2181)
│   ├── HPA
│   │   └── nova-api-hpa (min: 2, max: 10)
│   ├── ConfigMap: novadesk-config
│   ├── Secret: novadesk-secrets
│   └── PVC: postgres-pvc (5Gi)
```

## Manual Deployment Steps

```powershell
# Create cluster
kind create cluster --config production/k8s/kind-cluster.yaml --name novadesk

# Build and load image
docker build -f production/k8s/Dockerfile -t novadesk-api:latest .
kind load docker-image novadesk-api:latest --name novadesk

# Deploy
kubectl apply -f production/k8s/k8s-manifests.yaml

# Check pods
kubectl get pods -n novadesk
kubectl logs -n novadesk deployment/nova-api
```

## Update GROQ_API_KEY in Kubernetes

```powershell
kubectl create secret generic novadesk-secrets \
  --from-literal=GROQ_API_KEY=your_real_key \
  --namespace novadesk \
  --dry-run=client -o yaml | kubectl apply -f -
```

## Scaling

```powershell
# Scale API pods manually
kubectl scale deployment nova-api --replicas=5 -n novadesk

# HPA auto-scales based on CPU/memory
kubectl get hpa -n novadesk
```

## Cleanup

```powershell
kind delete cluster --name novadesk
```

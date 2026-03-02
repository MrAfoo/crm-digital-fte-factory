# NovaDeskAI Kubernetes Deployment Script (Kind)
# Usage: .\production\k8s\deploy.ps1

Write-Host ''
Write-Host '================================================' -ForegroundColor Cyan
Write-Host '  NovaDeskAI - Kubernetes Deployment (Kind)' -ForegroundColor Cyan  
Write-Host '================================================' -ForegroundColor Cyan
Write-Host ''

# Check prerequisites
function Check-Command($name) {
    if (-not (Get-Command $name -ErrorAction SilentlyContinue)) {
        Write-Host "[ERROR] $name not found. Please install it first." -ForegroundColor Red
        return $false
    }
    Write-Host "[OK] $name found" -ForegroundColor Green
    return $true
}

Write-Host '[1/6] Checking prerequisites...' -ForegroundColor Yellow
$ok = $true
$ok = $ok -and (Check-Command 'kind')
$ok = $ok -and (Check-Command 'kubectl')
$ok = $ok -and (Check-Command 'docker')
if (-not $ok) {
    Write-Host ''
    Write-Host 'Install missing tools:' -ForegroundColor Yellow
    Write-Host '  kind:    https://kind.sigs.k8s.io/docs/user/quick-start/#installation'
    Write-Host '  kubectl: https://kubernetes.io/docs/tasks/tools/'
    Write-Host '  docker:  https://docs.docker.com/get-docker/'
    exit 1
}
Write-Host ''

# Create Kind cluster
Write-Host '[2/6] Creating Kind cluster (novadesk)...' -ForegroundColor Yellow
$clusterExists = kind get clusters 2>&1 | Select-String 'novadesk'
if ($clusterExists) {
    Write-Host '      Cluster already exists, skipping...' -ForegroundColor DarkGray
} else {
    kind create cluster --config production/k8s/kind-cluster.yaml --name novadesk
    if ($LASTEXITCODE -ne 0) { Write-Host '[ERROR] Failed to create cluster' -ForegroundColor Red; exit 1 }
    Write-Host '      Kind cluster created!' -ForegroundColor Green
}
Write-Host ''

# Build Docker image
Write-Host '[3/6] Building Docker image...' -ForegroundColor Yellow
docker build -f production/k8s/Dockerfile -t novadesk-api:latest .
if ($LASTEXITCODE -ne 0) { Write-Host '[ERROR] Docker build failed' -ForegroundColor Red; exit 1 }
Write-Host '      Image built: novadesk-api:latest' -ForegroundColor Green
Write-Host ''

# Load image into Kind
Write-Host '[4/6] Loading image into Kind cluster...' -ForegroundColor Yellow
kind load docker-image novadesk-api:latest --name novadesk
Write-Host '      Image loaded into Kind!' -ForegroundColor Green
Write-Host ''

# Apply manifests
Write-Host '[5/6] Applying Kubernetes manifests...' -ForegroundColor Yellow
kubectl apply -f production/k8s/k8s-manifests.yaml
if ($LASTEXITCODE -ne 0) { Write-Host '[ERROR] kubectl apply failed' -ForegroundColor Red; exit 1 }
Write-Host '      Manifests applied!' -ForegroundColor Green
Write-Host ''

# Wait for deployments
Write-Host '[6/6] Waiting for pods to be ready...' -ForegroundColor Yellow
kubectl wait --namespace novadesk --for=condition=ready pod --selector=app=nova-api --timeout=120s
Write-Host '      Pods ready!' -ForegroundColor Green
Write-Host ''

# Summary
Write-Host '================================================' -ForegroundColor Cyan
Write-Host '  Deployment Complete!' -ForegroundColor Green
Write-Host '================================================' -ForegroundColor Cyan
Write-Host ''
Write-Host '  Pods:' -ForegroundColor White
kubectl get pods -n novadesk
Write-Host ''
Write-Host '  Services:' -ForegroundColor White
kubectl get services -n novadesk
Write-Host ''
Write-Host '  API URL: http://localhost:30800/health' -ForegroundColor Green
Write-Host '  Kafka:   kubectl port-forward -n novadesk svc/kafka-service 9092:9092' -ForegroundColor White
Write-Host ''
Write-Host '  To delete cluster: kind delete cluster --name novadesk' -ForegroundColor DarkGray
Write-Host ''

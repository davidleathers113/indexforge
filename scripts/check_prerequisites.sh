#!/bin/bash
set -e

# Source common functions
source ./scripts/common.sh

log "Checking prerequisites for Istio deployment..."

# Check required commands
REQUIRED_COMMANDS=(
    "kubectl"
    "istioctl"
    "jq"
    "curl"
    "openssl"
    "poetry"
)

for cmd in "${REQUIRED_COMMANDS[@]}"; do
    if ! command_exists "$cmd"; then
        error "$cmd not found. Please install $cmd first."
    fi
    log "✓ $cmd found"
done

# Check Kubernetes cluster access
log "Checking Kubernetes cluster access..."
if ! kubectl cluster-info &> /dev/null; then
    error "Unable to access Kubernetes cluster. Please check your kubeconfig."
fi
log "✓ Kubernetes cluster accessible"

# Check Kubernetes version compatibility
log "Checking Kubernetes version..."
K8S_VERSION=$(kubectl version --short | grep "Server Version" | cut -d " " -f3)
MIN_K8S_VERSION="v1.21.0"
if ! [[ "$(printf '%s\n' "$MIN_K8S_VERSION" "$K8S_VERSION" | sort -V | head -n1)" = "$MIN_K8S_VERSION" ]]; then
    error "Kubernetes version $K8S_VERSION is less than minimum required version $MIN_K8S_VERSION"
fi
log "✓ Kubernetes version $K8S_VERSION meets minimum requirement"

# Check Istio version compatibility
log "Checking Istio version..."
if ! check_istio_compatibility; then
    error "Istio version does not meet minimum requirements"
fi
log "✓ Istio version compatible"

# Check required permissions
log "Checking required permissions..."
REQUIRED_PERMISSIONS=(
    "create namespace --all-namespaces"
    "create deployment -n indexforge"
    "create service -n indexforge"
    "create configmap -n istio-system"
    "create secret -n istio-system"
)

for perm in "${REQUIRED_PERMISSIONS[@]}"; do
    if ! kubectl auth can-i $perm; then
        error "Insufficient permissions: cannot $perm"
    fi
    log "✓ Permission check passed: $perm"
done

# Check network connectivity
log "Checking network connectivity..."
REQUIRED_ENDPOINTS=(
    "https://storage.googleapis.com"
    "https://gcr.io"
    "https://github.com"
    "https://hub.docker.com"
)

for endpoint in "${REQUIRED_ENDPOINTS[@]}"; do
    if ! curl -s -m 5 $endpoint &> /dev/null; then
        log "Warning: Unable to reach $endpoint"
    else
        log "✓ $endpoint accessible"
    fi
done

# Check required namespaces
log "Checking namespaces..."
REQUIRED_NAMESPACES=(
    "indexforge"
    "istio-system"
)

for ns in "${REQUIRED_NAMESPACES[@]}"; do
    if ! check_namespace "$ns"; then
        log "Creating namespace: $ns"
        kubectl create namespace $ns
    fi
    log "✓ Namespace $ns exists"
done

# Check resource requirements
log "Checking cluster resources..."
AVAILABLE_CPU=$(kubectl get nodes -o jsonpath='{.items[*].status.allocatable.cpu}' | awk '{s+=$1} END {print s}')
AVAILABLE_MEMORY=$(kubectl get nodes -o jsonpath='{.items[*].status.allocatable.memory}' | awk '{s+=$1} END {print s}')

# Minimum requirements for Istio deployment
MIN_CPU=4    # 4 CPU cores
MIN_MEMORY=8589934592  # 8Gi in bytes

if ! check_resources $MIN_CPU $MIN_MEMORY; then
    log "Warning: Available resources (CPU: ${AVAILABLE_CPU}cores, Memory: ${AVAILABLE_MEMORY}bytes) are less than recommended (CPU: ${MIN_CPU}cores, Memory: ${MIN_MEMORY}bytes)"
fi
log "✓ Resource requirements checked"

# Check existing deployments
log "Checking existing deployments..."
if kubectl get deployment -n istio-system &> /dev/null; then
    log "Warning: Existing Istio deployment found. This script will modify the existing deployment."
fi

# Verify required directories and files
log "Checking required files..."
REQUIRED_FILES=(
    "istio/config/istio-operator.yaml"
    "istio/config/mtls-policy.yaml"
    "istio/config/network-policy.yaml"
)

for file in "${REQUIRED_FILES[@]}"; do
    if [ ! -f "$file" ]; then
        error "Required file $file not found"
    fi
    log "✓ File $file exists"
done

# Check Python environment
log "Checking Python environment..."
poetry install --only ci || error "Failed to install Python dependencies"
log "✓ Python dependencies installed"

# Check Docker environment
log "Checking Docker environment..."
if ! docker info &> /dev/null; then
    log "Warning: Docker not running or not accessible"
else
    log "✓ Docker is running"
fi

# Check disk space
log "Checking available disk space..."
AVAILABLE_SPACE=$(df -k . | awk 'NR==2 {print $4}')
MIN_SPACE=$((10 * 1024 * 1024)) # 10GB in KB
if [ "$AVAILABLE_SPACE" -lt "$MIN_SPACE" ]; then
    log "Warning: Available disk space (${AVAILABLE_SPACE}KB) is less than recommended (${MIN_SPACE}KB)"
fi
log "✓ Disk space checked"

log "All prerequisites checked. Ready to proceed with Istio deployment."
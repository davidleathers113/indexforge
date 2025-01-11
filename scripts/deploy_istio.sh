#!/bin/bash
set -e

# Source common functions
source ./scripts/common.sh

# Initialize variables
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
DEPLOY_LOG="$BACKUP_DIR/deploy.log"
RETRY_COUNT=3
RETRY_DELAY=10

# Create backup directory
mkdir -p $BACKUP_DIR

# Setup logging
exec 1> >(tee -a "$DEPLOY_LOG")
exec 2> >(tee -a "$DEPLOY_LOG" >&2)

# Backup function
backup_configurations() {
    log "Backing up existing configurations..."
    mkdir -p $BACKUP_DIR/configs

    # Backup existing Istio configurations
    if kubectl get namespace istio-system &> /dev/null; then
        kubectl get -n istio-system -o yaml \
            $(kubectl get -n istio-system -o name peerauthentications,destinationrules,gateways,virtualservices) \
            > $BACKUP_DIR/configs/istio-config-backup.yaml 2>/dev/null || true
        log "✓ Istio configurations backed up"
    fi

    # Backup existing network policies
    kubectl get networkpolicy -n indexforge -o yaml > $BACKUP_DIR/configs/network-policies-backup.yaml 2>/dev/null || true
    log "✓ Network policies backed up"
}

# Rollback function
rollback() {
    local exit_code=$?
    log "ERROR: Deployment failed with exit code $exit_code. Rolling back changes..."

    if [ -f "$BACKUP_DIR/configs/istio-config-backup.yaml" ]; then
        log "Restoring Istio configurations..."
        kubectl apply -f "$BACKUP_DIR/configs/istio-config-backup.yaml" || true
    fi

    if [ -f "$BACKUP_DIR/configs/network-policies-backup.yaml" ]; then
        log "Restoring network policies..."
        kubectl apply -f "$BACKUP_DIR/configs/network-policies-backup.yaml" || true
    fi

    # Remove Istio if it was newly installed
    if [ ! -f "$BACKUP_DIR/configs/istio-config-backup.yaml" ]; then
        log "Removing Istio installation..."
        kubectl delete namespace istio-system --ignore-not-found=true || true
    fi

    log "Rollback completed"
    exit 1
}

# Set trap for rollback
trap rollback ERR

# Validate Istio configuration
validate_istio_config() {
    log "Validating Istio configuration..."
    istioctl analyze -n istio-system || error "Istio configuration validation failed"
    istioctl analyze -n indexforge || error "Application namespace configuration validation failed"
    log "✓ Istio configuration validated"
}

# Check prerequisites
log "Checking prerequisites..."
./scripts/check_prerequisites.sh || error "Prerequisites check failed"

# Backup existing configurations
backup_configurations

log "Starting Istio deployment..."

# Create istio-system namespace
log "Creating istio-system namespace..."
kubectl create namespace istio-system --dry-run=client -o yaml | kubectl apply -f - || error "Failed to create namespace"
log "✓ Namespace created"

# Apply Istio Operator configuration
log "Applying Istio Operator configuration..."
kubectl apply -f istio/config/istio-operator.yaml || error "Failed to apply Istio Operator configuration"
log "✓ Operator configuration applied"

# Wait for Istio Operator to be ready
log "Waiting for Istio Operator to be ready..."
if ! kubectl wait --for=condition=Ready pod -l name=istio-operator -n istio-system --timeout=300s; then
    error "Timeout waiting for Istio Operator"
fi
log "✓ Operator ready"

# Validate initial configuration
validate_istio_config

# Apply mTLS policy with retries
log "Applying mTLS policy..."
for i in $(seq 1 $RETRY_COUNT); do
    if kubectl apply -f istio/config/mtls-policy.yaml; then
        log "✓ mTLS policy applied"
        break
    fi
    if [ $i -eq $RETRY_COUNT ]; then
        error "Failed to apply mTLS policy after $RETRY_COUNT attempts"
    fi
    log "Retrying mTLS policy application in $RETRY_DELAY seconds..."
    sleep $RETRY_DELAY
done

# Apply network policy with retries
log "Applying network policy..."
for i in $(seq 1 $RETRY_COUNT); do
    if kubectl apply -f istio/config/network-policy.yaml; then
        log "✓ Network policy applied"
        break
    fi
    if [ $i -eq $RETRY_COUNT ]; then
        error "Failed to apply network policy after $RETRY_COUNT attempts"
    fi
    log "Retrying network policy application in $RETRY_DELAY seconds..."
    sleep $RETRY_DELAY
done

# Verify Istio installation
log "Verifying Istio installation..."
REQUIRED_PODS=(
    "istiod"
    "istio-ingressgateway"
)

for pod in "${REQUIRED_PODS[@]}"; do
    if ! kubectl wait --for=condition=Ready pod -l app=$pod -n istio-system --timeout=300s; then
        error "Pod $pod is not running"
    fi
    log "✓ Pod $pod is running"
done

# Enable automatic sidecar injection
log "Enabling automatic sidecar injection for indexforge namespace..."
kubectl label namespace indexforge istio-injection=enabled --overwrite || error "Failed to enable sidecar injection"
log "✓ Sidecar injection enabled"

# Verify mTLS policy
log "Verifying mTLS policy..."
if ! kubectl get peerauthentication -n indexforge | grep -q "strict-mtls"; then
    error "mTLS policy not found"
fi
log "✓ mTLS policy verified"

if ! kubectl get destinationrule -n indexforge | grep -q "indexforge-services"; then
    error "Destination rule not found"
fi
log "✓ Destination rules verified"

# Verify network policy
log "Verifying network policy..."
if ! kubectl get networkpolicy -n indexforge | grep -q "restricted-access"; then
    error "Network policy not found"
fi
log "✓ Network policy verified"

# Restart deployments to inject sidecars
log "Restarting deployments to inject Istio sidecars..."
kubectl rollout restart deployment -n indexforge || log "Warning: Failed to restart deployments"
log "✓ Deployments restarted"

# Wait for deployments to be ready
log "Waiting for deployments to be ready..."
kubectl rollout status deployment -n indexforge --timeout=300s || error "Deployment rollout failed"
log "✓ Deployments ready"

# Verify Istio proxy injection
log "Verifying Istio proxy injection..."
PODS=$(kubectl get pods -n indexforge -o jsonpath='{.items[*].metadata.name}')
for POD in $PODS; do
    if ! kubectl get pod $POD -n indexforge -o jsonpath='{.spec.containers[*].name}' | grep -q "istio-proxy"; then
        error "Istio proxy not injected in pod $POD"
    fi
    log "✓ Istio proxy verified in pod $POD"
done

# Final validation
validate_istio_config

log "Istio deployment completed successfully. Deployment log available at: $DEPLOY_LOG"
log "Run verification tests with: ./scripts/test_istio.sh"
#!/bin/bash
set -e

# Source common functions
source ./scripts/common.sh

log() {
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')] $@"
}

error() {
    log "ERROR: $@" >&2
    exit 1
}

cleanup() {
    log "Cleaning up..."
    pkill -f "port-forward" || true
}

trap cleanup EXIT

log "Running Istio integration tests..."

# Ensure Istio is deployed
if ! kubectl get namespace istio-system &> /dev/null; then
    log "Istio is not deployed. Running deployment script..."
    ./scripts/deploy_istio.sh || error "Istio deployment failed"
fi

# Wait for all pods to be ready
log "Waiting for all pods to be ready..."
kubectl wait --for=condition=Ready pod --all -n istio-system --timeout=300s || error "Timeout waiting for Istio pods"
kubectl wait --for=condition=Ready pod --all -n indexforge --timeout=300s || error "Timeout waiting for application pods"

# Verify Istio injection
log "Verifying Istio sidecar injection..."
PODS=$(kubectl get pods -n indexforge -o jsonpath='{.items[*].metadata.name}')
for POD in $PODS; do
    if ! kubectl get pod $POD -n indexforge -o jsonpath='{.spec.containers[*].name}' | grep -q "istio-proxy"; then
        error "Istio proxy not injected in pod $POD"
    fi
done

# Run the integration tests
log "Running integration tests..."
if ! pytest tests/integration/test_istio_mesh.py -v --capture=no; then
    error "Integration tests failed"
fi

# Display Istio proxy status
log "Checking Istio proxy status..."
if ! istioctl proxy-status; then
    error "Istio proxy status check failed"
fi

# Show mTLS status
log "Checking mTLS status..."
PODS=$(kubectl get pod -l app=indexforge -o jsonpath='{.items..metadata.name}')
for POD in $PODS; do
    log "Checking mTLS for pod $POD..."
    if ! istioctl authn tls-check $POD; then
        error "mTLS check failed for pod $POD"
    fi
done

# Setup port-forwarding for metrics
log "Setting up port-forwarding for metrics collection..."
PROM_POD=$(kubectl -n istio-system get pod -l app=prometheus -o jsonpath='{.items[0].metadata.name}')
kubectl -n istio-system port-forward $PROM_POD 9090:9090 &
sleep 5

# Check basic metrics
log "Checking Istio metrics..."
METRICS=(
    "istio_requests_total"
    "istio_request_duration_milliseconds"
    "istio_response_bytes"
    "istio_tcp_connections_opened_total"
)

for METRIC in "${METRICS[@]}"; do
    log "Checking metric: $METRIC"
    if ! curl -s "http://localhost:9090/api/v1/query?query=$METRIC" | jq -e '.data.result | length > 0' > /dev/null; then
        log "Warning: No data found for metric $METRIC"
    fi
done

# Check security metrics
log "Checking security metrics..."
SECURITY_METRICS=(
    "istio_requests_total{response_code=~\"4.*|5.*\"}"
    "istio_authentication_failures_total"
)

for METRIC in "${SECURITY_METRICS[@]}"; do
    log "Checking security metric: $METRIC"
    if ! curl -s "http://localhost:9090/api/v1/query?query=$METRIC" | jq -e '.data.result | length >= 0' > /dev/null; then
        log "Warning: Unable to verify security metric $METRIC"
    fi
done

# Verify tracing
log "Verifying distributed tracing..."
if ! curl -s "http://localhost:16686/api/traces" > /dev/null; then
    log "Warning: Unable to verify Jaeger tracing"
fi

# Final verification
log "Running final verification checks..."

# Check service mesh connectivity
log "Checking service mesh connectivity..."
for SERVICE in $(kubectl get svc -n indexforge -o jsonpath='{.items[*].metadata.name}'); do
    log "Checking connectivity to service: $SERVICE"
    if ! kubectl exec -it deploy/app -n indexforge -c istio-proxy -- curl -s -o /dev/null -w "%{http_code}" http://$SERVICE:8000/health | grep -q "200"; then
        log "Warning: Unable to connect to service $SERVICE"
    fi
done

log "Istio testing complete"
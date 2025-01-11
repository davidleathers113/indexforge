#!/bin/bash

# Common logging function
log() {
    echo "[$(date +'%Y-%m-%dT%H:%M:%S%z')] $@"
}

# Error handling function
error() {
    log "ERROR: $@" >&2
    exit 1
}

# Function to check if a command exists
command_exists() {
    command -v "$1" &> /dev/null
}

# Function to check if a pod is ready
check_pod_ready() {
    local namespace=$1
    local pod=$2
    local timeout=${3:-300}

    kubectl wait --for=condition=Ready pod/$pod -n $namespace --timeout=${timeout}s
}

# Function to check if a service is ready
check_service_ready() {
    local namespace=$1
    local service=$2
    local port=${3:-8000}
    local timeout=${4:-30}
    local start_time=$(date +%s)

    while true; do
        if kubectl run -i --rm --restart=Never curl-test --image=curlimages/curl --namespace=$namespace -- \
            -s -o /dev/null -w "%{http_code}" http://$service:$port/health | grep -q "200"; then
            return 0
        fi

        if [ $(($(date +%s) - start_time)) -ge $timeout ]; then
            return 1
        fi
        sleep 1
    done
}

# Function to verify mTLS status
verify_mtls() {
    local namespace=$1
    local pod=$2

    istioctl authn tls-check $pod.$namespace
}

# Function to check metrics
check_metric() {
    local metric=$1
    local query="$2"
    local prometheus_port=${3:-9090}

    curl -s "http://localhost:$prometheus_port/api/v1/query?query=$query" | \
        jq -e '.data.result | length > 0' > /dev/null
}

# Function to setup port forwarding
setup_port_forward() {
    local namespace=$1
    local service=$2
    local local_port=$3
    local remote_port=$4

    kubectl port-forward -n $namespace svc/$service $local_port:$remote_port &
    sleep 2
}

# Function to check if namespace exists
check_namespace() {
    local namespace=$1
    kubectl get namespace $namespace &> /dev/null
}

# Function to check resource requirements
check_resources() {
    local cpu_request=$1
    local memory_request=$2

    local available_cpu=$(kubectl get nodes -o jsonpath='{.items[*].status.allocatable.cpu}' | \
        awk '{s+=$1} END {print s}')
    local available_memory=$(kubectl get nodes -o jsonpath='{.items[*].status.allocatable.memory}' | \
        awk '{s+=$1} END {print s}')

    if (( available_cpu < cpu_request )); then
        return 1
    fi

    if (( available_memory < memory_request )); then
        return 1
    fi

    return 0
}

# Function to check if a deployment is ready
check_deployment_ready() {
    local namespace=$1
    local deployment=$2
    local timeout=${3:-300}

    kubectl rollout status deployment/$deployment -n $namespace --timeout=${timeout}s
}

# Function to verify Istio injection
verify_istio_injection() {
    local namespace=$1
    local pod=$2

    kubectl get pod $pod -n $namespace -o jsonpath='{.spec.containers[*].name}' | \
        grep -q "istio-proxy"
}

# Function to cleanup resources
cleanup_resources() {
    pkill -f "port-forward" || true
    kubectl delete pod curl-test --ignore-not-found=true &> /dev/null || true
}

# Set trap for cleanup
trap cleanup_resources EXIT
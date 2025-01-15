from kubernetes import client, config
import pytest
import requests
from tenacity import retry, stop_after_attempt, wait_exponential


@pytest.fixture(scope="module")
def k8s_api():
    """Initialize Kubernetes API client."""
    config.load_kube_config()
    return client.CoreV1Api()


@pytest.fixture(scope="module")
def istio_api():
    """Initialize Istio API client."""
    return client.CustomObjectsApi()


def test_istio_pods_running(k8s_api):
    """Test that all Istio pods are running."""
    pods = k8s_api.list_namespaced_pod(namespace="istio-system")
    for pod in pods.items:
        assert pod.status.phase == "Running"
        for container in pod.status.container_statuses:
            assert container.ready is True


def test_mtls_policy_applied(istio_api):
    """Test that mTLS policy is applied correctly."""
    peer_auth = istio_api.get_namespaced_custom_object(
        group="security.istio.io",
        version="v1beta1",
        namespace="indexforge",
        plural="peerauthentications",
        name="strict-mtls",
    )
    assert peer_auth["spec"]["mtls"]["mode"] == "STRICT"


@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
def test_service_communication():
    """Test service-to-service communication with mTLS."""
    # Test app service health endpoint
    response = requests.get("http://localhost:8000/health", headers={"X-B3-Sampled": "1"})
    assert response.status_code == 200

    # Test ML service health endpoint
    response = requests.get("http://localhost:8001/health", headers={"X-B3-Sampled": "1"})
    assert response.status_code == 200


def test_network_policy(k8s_api):
    """Test that network policies are applied."""
    network_policies = k8s_api.list_namespaced_network_policy(namespace="indexforge")
    policy_found = False
    for policy in network_policies.items:
        if policy.metadata.name == "restricted-access":
            policy_found = True
            # Verify ingress rules
            assert len(policy.spec.ingress) > 0
            # Verify egress rules
            assert len(policy.spec.egress) > 0
    assert policy_found, "Network policy 'restricted-access' not found"


def test_istio_metrics():
    """Test that Istio metrics are being collected."""
    response = requests.get(
        "http://localhost:9090/api/v1/query", params={"query": "istio_requests_total"}
    )
    assert response.status_code == 200
    metrics = response.json()
    assert "data" in metrics
    assert len(metrics["data"]["result"]) > 0


@pytest.mark.asyncio
async def test_tracing_integration():
    """Test that distributed tracing is working."""
    # Make a request with tracing headers
    headers = {
        "X-B3-TraceId": "80f198ee56343ba864fe8b2a57d3eff7",
        "X-B3-ParentSpanId": "05e3ac9a4f6e3b90",
        "X-B3-SpanId": "e457b5a2e4d86bd1",
        "X-B3-Sampled": "1",
    }
    response = requests.get("http://localhost:8000/health", headers=headers)
    assert response.status_code == 200

    # Verify trace in Jaeger
    response = requests.get("http://localhost:16686/api/traces", params={"service": "app"})
    assert response.status_code == 200
    traces = response.json()
    assert len(traces["data"]) > 0

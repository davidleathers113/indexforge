# IndexForge Microservices Improvement Plan

## Current Architecture Assessment

### Strengths

- ✅ Well-defined service separation (app, ml-service, weaviate, t2v-transformers)
- ✅ Proper resource allocation and limits
- ✅ Health check implementation across services
- ✅ Clear deployment configurations
- ✅ Kong API Gateway integration with plugins
- ✅ Redis instance separation
- ✅ Basic observability stack with Prometheus, Grafana, and Jaeger

### Areas for Improvement

1. ✅ Database sharing between services (Completed with Redis separation)
2. ✅ Service coupling (Excel processing completed with dedicated processor)
3. ✅ Missing API Gateway (Completed with Kong CE)
4. ✅ Incomplete observability stack (Completed with comprehensive monitoring)
5. Domain boundary violations

## Implementation Phases

### Phase 1: Kong API Gateway Implementation (Weeks 1-2) ✅ COMPLETED

#### 1. Kong CE Gateway Setup ✅ COMPLETED

- ✅ Deploy Kong CE as the API Gateway
- ✅ Configure declarative routing (DB-less mode)
- ✅ Implement essential plugins
- ✅ Set up service discovery

```yaml
# Kong Gateway service configuration
services:
  api-gateway:
    image: kong:3.x
    container_name: kong
    environment:
      - KONG_DATABASE=off
      - KONG_PROXY_ACCESS_LOG=/dev/stdout
      - KONG_ADMIN_ACCESS_LOG=/dev/stdout
      - KONG_PROXY_ERROR_LOG=/dev/stderr
      - KONG_ADMIN_ERROR_LOG=/dev/stderr
      - KONG_ADMIN_LISTEN=0.0.0.0:8001
    ports:
      - "8000:8000" # Proxy port
      - "8443:8443" # Proxy SSL port
      - "8001:8001" # Admin API
      - "8444:8444" # Admin SSL
    volumes:
      - ./kong.yml:/usr/local/kong/declarative/kong.yml
    networks:
      - indexforge-network
    healthcheck:
      test: ["CMD", "kong", "health"]
      interval: 10s
      timeout: 10s
      retries: 3
```

```yaml
# kong.yml - Declarative configuration
_format_version: "3.0"
_transform: true

services:
  - name: app-service
    url: http://app:8000
    routes:
      - name: app-routes
        paths:
          - /api/v1/
    plugins:
      - name: rate-limiting
        config:
          minute: 60
          policy: local
      - name: cors
      - name: prometheus

  - name: ml-service
    url: http://ml-service:8001
    routes:
      - name: ml-routes
        paths:
          - /api/v1/ml/
    plugins:
      - name: rate-limiting
        config:
          minute: 30
          policy: local
      - name: cors
      - name: prometheus

consumers:
  - username: api-consumer
    keyauth_credentials:
      - key: your-secret-key

plugins:
  - name: key-auth
    config:
      key_names:
        - apikey
  - name: proxy-cache
    config:
      content_type:
        - "application/json"
      cache_ttl: 300
      strategy: memory
  - name: correlation-id
    config:
      header_name: Kong-Request-ID
      generator: uuid#counter
      echo_downstream: true
```

#### 2. Essential Kong CE Plugin Configuration

1. **Authentication**

   - Key Authentication
   - IP Restriction
   - Basic Auth (if needed)

2. **Traffic Control**

   - Rate Limiting
   - Proxy Caching
   - Circuit Breaker

3. **Observability**

   - Prometheus Metrics
   - Request/Response Logging
   - Correlation IDs

4. **Security**
   - CORS
   - Bot Detection
   - IP Restriction

#### 3. Service Integration

1. **Route Configuration**

   - Map external paths to services
   - Configure path prefixes
   - Set up SSL termination

2. **Health Checks**

   - Active health checking
   - Passive health checking
   - Circuit breaking

3. **Load Balancing**
   - Round-robin balancing
   - Health check-aware
   - Sticky sessions if needed

#### 4. Monitoring Setup

1. **Metrics Collection**

   - Request/response latency
   - Error rates
   - Request volume

2. **Logging**

   - Access logs
   - Error logs
   - Debug logs when needed

3. **Alerting**
   - Error rate thresholds
   - Latency thresholds
   - Health check failures

### Phase 2: Service Boundary Realignment (Weeks 3-4) ✅ COMPLETED

#### 1. Excel Processing ✅ COMPLETED

- ✅ Implemented dedicated Excel processor with comprehensive functionality
- ✅ Created Excel processing API endpoints
- ✅ Added proper error handling and retries
- ✅ Integrated with document processing pipeline

#### 2. Database Independence ✅ COMPLETED

##### Redis Instance Separation ✅ COMPLETED

- ✅ Separate Redis instances per service
- ✅ Isolation of data concerns
- ✅ Independent scaling
- ✅ Service-specific optimization

```yaml
services:
  # Main application Redis
  app-redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 512mb --maxmemory-policy allkeys-lru
    volumes:
      - app_redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: "0.5"
          memory: 768M
        reservations:
          memory: 256M
    networks:
      - indexforge-network

  # ML Service Redis
  ml-redis:
    image: redis:7-alpine
    command: redis-server --appendonly yes --maxmemory 1gb --maxmemory-policy volatile-lru
    volumes:
      - ml_redis_data:/data
    ports:
      - "6380:6379" # Different port to avoid conflicts
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      timeout: 3s
      retries: 3
    deploy:
      resources:
        limits:
          cpus: "1"
          memory: 1.5G
        reservations:
          memory: 512M
    networks:
      - indexforge-network

volumes:
  app_redis_data:
  ml_redis_data:
```

##### Service-Specific Caching Strategies

1. **Main Application Cache (app-redis)**

   - Purpose: API response caching, session management
   - Configuration:
     ```conf
     maxmemory 512mb
     maxmemory-policy allkeys-lru  # Evict any key using LRU
     appendonly yes                # Data persistence
     ```
   - Cache Patterns:
     - Short-lived API response cache (TTL: 5 minutes)
     - Session data (TTL: 24 hours)
     - Rate limiting counters (TTL: 1 hour)
   - Implementation:

     ```python
     # FastAPI caching example
     from fastapi_cache import FastAPICache
     from fastapi_cache.backends.redis import RedisBackend

     @app.on_event("startup")
     async def startup():
         redis = aioredis.from_url(
             "redis://app-redis:6379",
             encoding="utf8",
             decode_responses=True
         )
         FastAPICache.init(
             RedisBackend(redis),
             prefix="app-cache:"
         )
     ```

2. **ML Service Cache (ml-redis)**

   - Purpose: Model results, computation cache
   - Configuration:
     ```conf
     maxmemory 1gb
     maxmemory-policy volatile-lru  # Evict only keys with TTL
     appendonly yes
     ```
   - Cache Patterns:
     - Model prediction results (TTL: 1 hour)
     - Processed Excel data (TTL: 30 minutes)
     - Computation results (TTL: 2 hours)
   - Implementation:

     ```python
     # ML service caching example
     from functools import lru_cache
     from redis import Redis

     class MLServiceCache:
         def __init__(self):
             self.redis = Redis(
                 host='ml-redis',
                 port=6379,
                 decode_responses=True
             )

         async def cache_prediction(self, input_hash: str, result: dict):
             await self.redis.setex(
                 f"pred:{input_hash}",
                 3600,  # 1 hour TTL
                 json.dumps(result)
             )
     ```

##### Cache Optimization Strategies

1. **Main Application (app-redis)**

   - Use cache tags for grouped invalidation
   - Implement stale-while-revalidate pattern
   - Cache serialization with MessagePack
   - Implement cache warming for common requests

2. **ML Service (ml-redis)**
   - Implement predictive prefetching
   - Cache model weights selectively
   - Use sliding window for time-series data
   - Implement cache stampede prevention

##### Monitoring and Maintenance

1. **Cache Metrics**

   ```yaml
   # Prometheus metrics
   - cache_hit_ratio
   - memory_usage
   - eviction_rate
   - connection_count
   ```

2. **Cache Management**
   - Regular cache pruning
   - Automated cache warming
   - Error rate monitoring
   - Cache invalidation logs

##### Failure Handling

1. **Circuit Breaking**

   ```python
   from tenacity import retry, stop_after_attempt

   @retry(stop=stop_after_attempt(3))
   async def get_cached_data(key: str):
       try:
           return await redis.get(key)
       except RedisError:
           # Fallback to computation
           return await compute_data()
   ```

2. **Fallback Strategies**
   - Local memory cache fallback
   - Compute-through on cache miss
   - Graceful degradation
   - Cache rebuild mechanisms

### Phase 3: Observability Enhancement (Weeks 5-6) ✅ COMPLETED

#### 1. Sentry Optimization ✅ COMPLETED

- ✅ Enhance error grouping and fingerprinting
- ✅ Implement performance monitoring
- ✅ Add custom contexts for better debugging
- ✅ Configure sampling rates per environment

```python
# Enhanced Sentry configuration
def init_sentry():
    sentry_sdk.init(
        dsn=settings.SENTRY_DSN,
        environment=settings.ENVIRONMENT,
        release=settings.VERSION,
        traces_sample_rate=0.1,  # Sample 10% of transactions
        profiles_sample_rate=0.1,  # Sample 10% of profiles
        _experiments={
            "profiles_sample_rate": 0.1
        },
        before_send=before_send_handler,
        before_breadcrumb=before_breadcrumb_handler,
        integrations=[
            FastApiIntegration(
                transaction_style="endpoint",
                transaction_name_callback=get_transaction_name
            ),
            RedisIntegration(
                connect_string=True,
                trace_queries=True
            ),
            SqlalchemyIntegration(
                connect_string=True,
                trace_queries=True
            ),
            LoggingIntegration(
                level=logging.INFO,
                event_level=logging.ERROR
            )
        ]
    )

def before_send_handler(event, hint):
    if 'exc_info' in hint:
        exc_type, exc_value, tb = hint['exc_info']

        # Add ML-specific context
        if 'ml_service' in event.get('transaction', ''):
            event['contexts']['ml'] = {
                'model_version': settings.ML_MODEL_VERSION,
                'batch_size': settings.BATCH_SIZE,
                'device': 'gpu' if torch.cuda.is_available() else 'cpu'
            }

        # Custom fingerprinting for common errors
        if isinstance(exc_value, ValueError):
            event['fingerprint'] = ['value-error', str(exc_value)]

    return event
```

#### 2. Service-Specific Performance Monitoring ✅ COMPLETED

1. **API Service Monitoring**

   - Request latency tracking
   - Endpoint usage patterns
   - Error rate monitoring
   - Resource utilization

2. **ML Service Monitoring**

   - Model inference times
   - Batch processing metrics
   - Memory usage tracking
   - GPU utilization (if applicable)

3. **Custom Metrics**

```python
# Custom performance metrics
from sentry_sdk import metrics

def track_ml_performance(model_name: str, batch_size: int, processing_time: float):
    metrics.timing(
        key="ml.inference.duration",
        value=processing_time,
        tags={
            "model": model_name,
            "batch_size": batch_size
        }
    )

    metrics.distribution(
        key="ml.batch.size",
        value=batch_size,
        unit="items"
    )
```

#### 3. Enhanced Error Tracking ✅ COMPLETED

1. **Error Categorization**

   - Service-specific error types
   - Error severity levels
   - Custom error contexts
   - Error frequency tracking

2. **Error Response Strategy**

```python
from sentry_sdk import capture_exception, set_context

def handle_processing_error(error: Exception, document_id: str, context: dict):
    set_context("document", {
        "id": document_id,
        "type": context.get("type"),
        "size": context.get("size")
    })

    set_context("processing", {
        "stage": context.get("stage"),
        "attempt": context.get("attempt"),
        "batch_id": context.get("batch_id")
    })

    capture_exception(error)
```

#### 4. Automated Performance Alerts ✅ COMPLETED

1. **Alert Configuration**

   ```python
   PERFORMANCE_THRESHOLDS = {
       "p95_latency_ms": 500,
       "error_rate": 0.01,
       "memory_usage": 0.85,
       "cpu_usage": 0.80
   }
   ```

2. **Alert Channels**

   - Email notifications
   - Slack integration
   - PagerDuty integration
   - Custom webhook support

3. **Alert Rules**
   - Latency thresholds
   - Error rate spikes
   - Resource exhaustion
   - Custom business metrics

#### 5. Comprehensive Monitoring Stack ✅ COMPLETED

##### A. Distributed Tracing with Jaeger ✅ COMPLETED

```yaml
# docker-compose.yml additions
services:
  jaeger:
    image: jaegertracing/all-in-one:1.47
    environment:
      - COLLECTOR_ZIPKIN_HOST_PORT=:9411
      - COLLECTOR_OTLP_ENABLED=true
    ports:
      - "6831:6831/udp" # Jaeger thrift compact
      - "16686:16686" # Web UI
      - "4317:4317" # OTLP gRPC
      - "4318:4318" # OTLP HTTP
    networks:
      - indexforge-network
```

```python
# Jaeger integration in services
from opentelemetry import trace
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

def setup_jaeger_tracing(app: FastAPI, service_name: str):
    # Set up the tracer
    tracer_provider = TracerProvider()
    jaeger_exporter = JaegerExporter(
        agent_host_name="jaeger",
        agent_port=6831,
    )
    tracer_provider.add_span_processor(
        BatchSpanProcessor(jaeger_exporter)
    )
    trace.set_tracer_provider(tracer_provider)

    # Instrument FastAPI
    FastAPIInstrumentor.instrument_app(
        app,
        tracer_provider=tracer_provider,
    )

# Example custom span
async def process_document(document_id: str):
    tracer = trace.get_tracer(__name__)
    with tracer.start_as_current_span("process_document") as span:
        span.set_attribute("document_id", document_id)
        # Processing logic here
```

##### B. Metrics Collection with Prometheus ✅ COMPLETED

```yaml
# docker-compose.yml additions
services:
  prometheus:
    image: prom/prometheus:v2.45.0
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - "--config.file=/etc/prometheus/prometheus.yml"
      - "--storage.tsdb.path=/prometheus"
      - "--web.console.libraries=/usr/share/prometheus/console_libraries"
      - "--web.console.templates=/usr/share/prometheus/consoles"
    ports:
      - "9090:9090"
    networks:
      - indexforge-network
```

```yaml
# prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  - job_name: "api-gateway"
    static_configs:
      - targets: ["kong:8001"]
    metrics_path: /metrics

  - job_name: "app-service"
    static_configs:
      - targets: ["app:8000"]
    metrics_path: /metrics

  - job_name: "ml-service"
    static_configs:
      - targets: ["ml-service:8001"]
    metrics_path: /metrics

  - job_name: "redis"
    static_configs:
      - targets: ["redis-exporter:9121"]
```

```python
# Service metrics implementation
from prometheus_client import Counter, Histogram, Info
from prometheus_fastapi_instrumentator import Instrumentator

# Custom metrics
REQUESTS_TOTAL = Counter(
    "app_requests_total",
    "Total count of requests by method and path",
    ["method", "path"]
)

REQUESTS_LATENCY = Histogram(
    "app_requests_latency_seconds",
    "Request latency in seconds",
    ["method", "path"]
)

ML_MODEL_INFO = Info(
    "ml_model_info",
    "ML model information"
)

def setup_prometheus_metrics(app: FastAPI):
    # Initialize instrumentator
    Instrumentator().instrument(app).expose(app)

    # Add custom metrics
    @app.middleware("http")
    async def track_requests(request: Request, call_next):
        REQUESTS_TOTAL.labels(
            method=request.method,
            path=request.url.path
        ).inc()

        with REQUESTS_LATENCY.labels(
            method=request.method,
            path=request.url.path
        ).time():
            response = await call_next(request)
            return response
```

##### C. Visualization with Grafana ✅ COMPLETED

```yaml
# docker-compose.yml additions
services:
  grafana:
    image: grafana/grafana:10.0.0
    volumes:
      - grafana_data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin_password
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    networks:
      - indexforge-network
```

```yaml
# grafana/provisioning/datasources/prometheus.yml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
```

```json
// grafana/provisioning/dashboards/ml_service.json
{
  "dashboard": {
    "title": "ML Service Metrics",
    "panels": [
      {
        "title": "Model Inference Latency",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(ml_model_inference_seconds_sum[5m]) / rate(ml_model_inference_seconds_count[5m])",
            "legendFormat": "{{model}}"
          }
        ]
      },
      {
        "title": "Request Rate",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(app_requests_total{path=~\"/api/v1/ml/.*\"}[5m])) by (path)",
            "legendFormat": "{{path}}"
          }
        ]
      }
    ]
  }
}
```

##### D. Integration Points

1. **Service-to-Tracing Integration**

   - OpenTelemetry SDK in each service
   - Automatic instrumentation for frameworks
   - Custom span creation for business logic

2. **Metrics Collection Points**

   - Service endpoints (/metrics)
   - Infrastructure metrics
   - Business metrics
   - Custom metrics

3. **Dashboard Organization**
   - Service-specific dashboards
   - Cross-service overview
   - Infrastructure metrics
   - Business KPIs

##### E. Alert Configuration

```yaml
# prometheus/alerts.yml
groups:
  - name: service_alerts
    rules:
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{status=~"5.."}[5m]))
          /
          sum(rate(http_requests_total[5m])) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
          description: Error rate is above 1% for 5 minutes

      - alert: SlowResponses
        expr: |
          histogram_quantile(0.95,
            sum(rate(http_request_duration_seconds_bucket[5m])) by (le)
          ) > 0.5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: Slow response times detected
          description: 95th percentile of response times is above 500ms
```

##### F. Monitoring Best Practices

1. **Data Retention**

   - Prometheus: 15 days retention
   - Jaeger: 7 days retention
   - Grafana snapshots for long-term storage

2. **Resource Requirements**

   ```yaml
   services:
     prometheus:
       deploy:
         resources:
           limits:
             cpus: "1"
             memory: 2G
           reservations:
             memory: 1G

     jaeger:
       deploy:
         resources:
           limits:
             cpus: "1"
             memory: 2G
           reservations:
             memory: 1G

     grafana:
       deploy:
         resources:
           limits:
             cpus: "0.5"
             memory: 1G
           reservations:
             memory: 512M
   ```

3. **Backup Strategy**

   ```bash
   # Prometheus data backup
   docker run --rm \
     --volumes-from prometheus \
     -v $(pwd)/backup:/backup \
     alpine tar czf /backup/prometheus-$(date +%Y%m%d).tar.gz /prometheus

   # Grafana backup
   docker run --rm \
     --volumes-from grafana \
     -v $(pwd)/backup:/backup \
     alpine tar czf /backup/grafana-$(date +%Y%m%d).tar.gz /var/lib/grafana
   ```

### Phase 4: Event-Driven Architecture (Weeks 7-8) 🔄 NOT STARTED

#### 1. Message Queue Implementation

- Deploy RabbitMQ or Apache Kafka
- Implement event-driven communication
- Add message schemas and validation

```yaml
services:
  rabbitmq:
    image: rabbitmq:3-management
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "check_port_connectivity"]
```

### Phase 5: Security Enhancements (Weeks 9-10) 🔄 NOT STARTED

#### 1. Service Mesh Implementation

- Deploy Istio service mesh
- Configure mTLS between services
- Implement traffic policies

#### 2. Secrets Management

- Deploy HashiCorp Vault
- Migrate sensitive configurations
- Implement secret rotation

```yaml
services:
  vault:
    image: vault:1.x
    cap_add:
      - IPC_LOCK
```

## Implementation Guidelines

### Service Communication

1. Use HTTP/2 for synchronous communication
2. Implement circuit breakers
3. Add proper timeout handling
4. Use correlation IDs for request tracking

### Monitoring Requirements

1. Service health metrics
2. Business metrics
3. System metrics
4. Custom alerts

### Security Standards

1. Regular security scanning
2. Dependency updates
3. Network policy enforcement
4. Access control auditing

## Success Metrics

### Performance

- Service response times < 200ms
- API gateway latency < 50ms
- 99.9% uptime

### Reliability

- Zero single points of failure
- Automatic failover capability
- < 1min recovery time

### Scalability

- Horizontal scaling capability
- Resource utilization < 70%
- No performance degradation under load

## Maintenance Plan

### Regular Tasks

1. Weekly dependency updates
2. Monthly security audits
3. Quarterly capacity planning
4. Continuous monitoring review

### Documentation Requirements

1. API specifications (OpenAPI)
2. Architecture diagrams
3. Runbooks
4. Incident response procedures

## Risk Mitigation

### Potential Risks

1. Service discovery failures
2. Database connection issues
3. Message queue bottlenecks
4. Resource exhaustion

### Mitigation Strategies

1. Circuit breakers
2. Fallback mechanisms
3. Rate limiting
4. Auto-scaling policies

## Timeline and Resources

### Timeline

- Total duration: 8 weeks
- Weekly sprints
- Daily standups
- Bi-weekly reviews

### Resource Requirements

- DevOps engineers
- Backend developers
- SRE team
- Security team

## Conclusion

This improvement plan addresses the current architectural gaps and provides a clear path to a more robust, scalable, and maintainable microservices architecture. Regular reviews and adjustments will be necessary during implementation to ensure all objectives are met.

# Source Tracking and Multi-Tenancy

This module provides comprehensive functionality for managing source-specific configurations, multi-tenancy support, document lineage tracking, and cross-referencing in the direct documentation indexing system.

## Core Components

### Source Tracking

- Source-specific schema variations
- Custom property sets per source type
- Vectorizer configuration customization
- Cross-source mapping support
- Configuration persistence and validation

### Multi-Tenancy

- Tenant isolation with configurable levels
- Tenant-specific schema overrides
- Custom property sets per tenant
- Cross-tenant search capabilities
- Tenant-specific vectorizer settings

### Document Lineage

- Processing step tracking
- Transformation history
- Error logging and monitoring
- Performance metrics collection
- Health check integration

### Cross-References

- Sequential reference tracking
- Semantic similarity analysis
- Topic-based clustering
- Bidirectional references
- Reference validation
- Circular reference detection

### Alert Management

- Multiple alert types (error, resource, performance, health)
- Configurable severity levels
- Email notifications
- Webhook integrations
- Alert cooldown management
- Threshold-based triggering

## Usage Examples

### Source Configuration

```python
from src.connectors.direct_documentation_indexing.source_tracking import SourceTracker

# Initialize source tracker
tracker = SourceTracker("word")

# Get source-specific schema
schema = tracker.get_schema()

# Update source configuration
tracker.update_config({
    "schema_variations": {
        "class": "CustomWordDocument",
        "description": "Custom Word document class"
    }
})
```

### Multi-Tenant Configuration

```python
from src.connectors.direct_documentation_indexing.source_tracking import TenantSourceTracker

# Initialize tenant-aware tracker
tracker = TenantSourceTracker("tenant_123", "word")

# Get tenant-specific schema
schema = tracker.get_schema()

# Update tenant configuration
tracker.update_tenant_config({
    "cross_tenant_search": True,
    "isolation_level": "flexible"
})

# Get search filters for tenant isolation
filters = tracker.get_search_filters()
```

### Cross-Reference Management

```python
from src.connectors.direct_documentation_indexing.source_tracking import CrossReferenceManager
import numpy as np

# Initialize manager
manager = CrossReferenceManager(
    similarity_threshold=0.8,
    max_semantic_refs=3,
    n_topics=5
)

# Add document chunks
chunk_ids = ["chunk1", "chunk2", "chunk3"]
embeddings = np.random.rand(3, 128)  # Example embeddings
for chunk_id, embedding in zip(chunk_ids, embeddings):
    manager.add_chunk(chunk_id, embedding)

# Establish references
manager.establish_sequential_references(chunk_ids)
manager.establish_semantic_references()
manager.establish_topic_references()

# Get references for a chunk
refs = manager.get_references("chunk1")
```

### Alert Management

```python
from src.connectors.direct_documentation_indexing.source_tracking import AlertManager, AlertType, AlertSeverity

# Initialize alert manager
manager = AlertManager(config_path="/path/to/config.json")

# Send critical alert
manager.send_alert(
    alert_type=AlertType.ERROR,
    severity=AlertSeverity.CRITICAL,
    message="Database connection failed",
    metadata={"error": "Connection timeout"}
)

# Monitor system health
health_data = get_system_health()
manager.check_and_alert(health_data)
```

## Configuration Files

### Source Configuration (configs/word_source.json)

```json
{
  "schema_variations": {
    "class": "WordDocument",
    "description": "Document from word source",
    "vectorizer": "text2vec-transformers"
  },
  "custom_properties": {
    "word_metadata": {
      "dataType": ["text"],
      "description": "Word document specific metadata"
    }
  },
  "vectorizer_settings": {
    "model": "sentence-transformers-all-MiniLM-L6-v2",
    "poolingStrategy": "mean"
  },
  "cross_source_mappings": {
    "excel": "document_id"
  }
}
```

### Tenant Configuration (tenant_configs/tenant_123.json)

```json
{
  "tenant_id": "tenant_123",
  "schema_overrides": {
    "description": "Custom tenant description"
  },
  "property_overrides": {
    "custom_field": {
      "dataType": ["text"],
      "description": "Tenant-specific field"
    }
  },
  "vectorizer_overrides": {
    "model": "custom-model"
  },
  "cross_tenant_search": true,
  "isolation_level": "flexible"
}
```

### Alert Configuration (configs/alerts.json)

```json
{
  "error_rate_threshold": 0.1,
  "memory_critical_threshold": 90.0,
  "alert_cooldown": 300,
  "email_config": {
    "smtp_host": "smtp.example.com",
    "smtp_port": "587",
    "from_address": "alerts@example.com",
    "to_address": "admin@example.com"
  },
  "webhook_urls": {
    "slack": "https://hooks.slack.com/services/...",
    "teams": "https://webhook.office.com/..."
  }
}
```

## Best Practices

### Source Configuration

- Use descriptive class names
- Include comprehensive property descriptions
- Validate schema before deployment
- Document cross-source mappings

### Tenant Management

- Use unique tenant identifiers
- Start with strict isolation
- Document tenant-specific customizations
- Monitor cross-tenant search usage

### Cross-References

- Choose appropriate similarity thresholds
- Limit semantic references per chunk
- Validate references regularly
- Monitor clustering quality

### Alert Management

- Configure appropriate thresholds
- Set reasonable cooldown periods
- Use descriptive alert messages
- Include relevant metadata

### Performance

- Cache frequently used configurations
- Optimize vectorizer settings per tenant
- Monitor resource usage per tenant
- Use appropriate batch sizes
- Implement alert cooldowns

## Testing

The module includes comprehensive tests covering:

- Default configuration handling
- Custom configuration loading
- Schema validation
- Tenant isolation
- Configuration updates
- Search filter generation
- Cross-reference validation
- Alert management
- Performance monitoring

Run tests using pytest:

```bash
pytest tests/connectors/direct_documentation_indexing/source_tracking/
```

## Error Handling

The module implements robust error handling for:

- Configuration loading failures
- Schema validation errors
- Tenant isolation breaches
- Reference validation issues
- Alert delivery failures
- Resource monitoring errors

## Monitoring and Maintenance

Regular monitoring should include:

- Alert frequency and patterns
- Resource usage per tenant
- Cross-reference quality
- Topic clustering effectiveness
- System health metrics
- Error rates and types

## Contributing

When contributing to this module:

1. Follow the existing code style
2. Add comprehensive docstrings
3. Update relevant tests
4. Document configuration changes
5. Test multi-tenant scenarios
6. Validate error handling

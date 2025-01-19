# Reference System Documentation

This document provides detailed information about the reference system implementation, including caching, classification, and performance optimizations.

## Overview

The reference system manages relationships between content chunks, providing features for:

- Bi-directional references
- Reference type classification
- Efficient caching
- Performance monitoring

## 1. Reference Types

### Direct References

- **Citations**: Direct quotes and explicit references
- **Links**: URL and cross-document links
- **Content Continuation**: Sequential content relationships

### Indirect References

- **Semantic Similarity**: Content-based relationships
- **Context-based**: Shared context or topic
- **Topic Relationships**: Clustered content relationships

### Structural References

- **Parent-Child**: Hierarchical document structure
- **Sequential**: Next/previous relationships
- **Table of Contents**: Document organization

## 2. Reference Classification

The system uses evidence-based classification to categorize references:

```python
# Example: Classifying a reference
classifier = ReferenceClassifier(ref_manager)
classification = classifier.classify_reference(source_id, target_id, ref_type)

# Classification includes:
- category: ReferenceCategory (DIRECT, INDIRECT, STRUCTURAL)
- confidence: float (0-1)
- evidence: Dict of supporting evidence
- metadata: Enriched reference metadata
```

### Classification Features

- Evidence-based categorization
- Confidence scoring
- Metadata enrichment
- Bidirectional reference handling

## 3. Reference Caching

The caching system optimizes reference access with:

### LRU Cache Implementation

```python
# Example: Using the reference cache
cache = ReferenceCache(ref_manager, maxsize=1000)
reference = cache.get_reference(source_id, target_id)
```

### Features

- Configurable cache size
- LRU eviction policy
- Forward/reverse indices
- Bidirectional reference handling
- Cache statistics tracking

### Cache Invalidation

- Single reference invalidation
- Chunk-level invalidation
- Cache clearing
- Statistics monitoring

### Performance Monitoring

```python
# Example: Monitoring cache performance
stats = cache.get_stats()
print(f"Hit rate: {stats.hit_rate}%")
print(f"Total requests: {stats.total_requests}")
print(f"Invalidations: {stats.invalidations}")
```

## 4. Performance Optimizations

### Memory Efficiency

- Lightweight data structures
- Efficient indexing
- Configurable cache limits

### Access Patterns

- Forward/reverse index optimization
- Batch reference operations
- Cache pre-warming capabilities

### Monitoring

- Cache hit/miss tracking
- Invalidation statistics
- Memory usage monitoring

## 5. Best Practices

### Configuration

```python
# Recommended cache configuration
cache = ReferenceCache(
    ref_manager,
    maxsize=min(total_chunks // 4, 10000)  # Balance memory and performance
)
```

### Usage Patterns

1. **Bulk Operations**

   ```python
   # Efficient bulk reference creation
   for source, target in chunk_pairs:
       ref_manager.add_reference(source, target, ref_type)
       cache.cache_reference(source, target, ref)
   ```

2. **Cache Maintenance**

   ```python
   # Regular cache maintenance
   if cache.stats.hit_rate < 30:
       cache.clear()  # Reset if hit rate is too low
   ```

3. **Reference Validation**
   ```python
   # Validate references periodically
   invalid_refs = ref_manager.validate_references()
   for ref in invalid_refs:
       cache.invalidate_reference(ref.source_id, ref.target_id)
   ```

## 6. Performance Considerations

### Memory Usage

- Cache size should be tuned based on available memory
- Monitor cache statistics to optimize size
- Use chunk-level invalidation for large updates

### Response Time

- Cache hit rates > 80% indicate good performance
- Pre-warm cache for frequently accessed references
- Use batch operations for bulk updates

### Scalability

- Cache scales well up to millions of references
- Forward/reverse indices optimize lookups
- Efficient memory usage through LRU policy

## 7. Monitoring and Maintenance

### Cache Monitoring

```python
# Regular monitoring
stats = cache.get_stats()
if stats.hit_rate < threshold:
    logger.warning(f"Low cache hit rate: {stats.hit_rate}%")
```

### Health Checks

```python
# Reference health monitoring
health_check = ReferenceHealthCheck(ref_manager)
issues = health_check.check_references()
for issue in issues:
    logger.error(f"Reference issue: {issue}")
```

### Performance Metrics

- Cache hit/miss rates
- Response times
- Memory usage
- Invalidation frequency

## 8. Integration Examples

### Basic Usage

```python
# Initialize components
ref_manager = ReferenceManager()
cache = ReferenceCache(ref_manager)
classifier = ReferenceClassifier(ref_manager)

# Create and classify reference
source_id = ref_manager.add_chunk("Source content")
target_id = ref_manager.add_chunk("Target content")
ref = ref_manager.add_reference(source_id, target_id, ReferenceType.CITATION)
classification = classifier.classify_reference(source_id, target_id, ref.ref_type)

# Access cached reference
cached_ref = cache.get_reference(source_id, target_id)
```

### Advanced Usage

```python
# Batch reference creation with classification
def process_chunk_relationships(chunks, similarity_threshold=0.8):
    for chunk1, chunk2, similarity in find_similar_chunks(chunks):
        if similarity >= similarity_threshold:
            ref = ref_manager.add_reference(
                chunk1.id,
                chunk2.id,
                ReferenceType.SIMILAR,
                metadata={"similarity_score": similarity}
            )
            cache.cache_reference(chunk1.id, chunk2.id, ref)
            classifier.update_reference_metadata(chunk1.id, chunk2.id)
```

## 9. Troubleshooting

### Common Issues

1. **Low Cache Hit Rate**

   - Increase cache size
   - Review access patterns
   - Consider pre-warming cache

2. **High Memory Usage**

   - Reduce cache size
   - Implement more aggressive invalidation
   - Monitor reference growth

3. **Slow Reference Lookups**
   - Check cache hit rate
   - Optimize batch operations
   - Review index usage

### Diagnostics

```python
# Cache diagnostics
def diagnose_cache_performance(cache):
    stats = cache.get_stats()
    return {
        "hit_rate": stats.hit_rate,
        "total_requests": stats.total_requests,
        "invalidations": stats.invalidations,
        "cache_size": len(cache.reference_cache),
        "forward_index_size": sum(len(v) for v in cache.forward_index.values()),
        "reverse_index_size": sum(len(v) for v in cache.reverse_index.values())
    }
```

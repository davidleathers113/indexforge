"""Pipeline step definitions.

This module defines the available processing steps in the pipeline using an
enumeration. Each step represents a distinct phase of document processing,
from loading to indexing.

Steps:
1. LOAD:
   - Load documents from export directory
   - Parse document structure
   - Extract basic metadata
   - Validate document format

2. DEDUPLICATE:
   - Detect duplicate documents
   - Remove redundant content
   - Maintain document relationships
   - Track duplicate statistics

3. PII:
   - Detect personally identifiable information
   - Apply redaction rules
   - Log PII findings
   - Ensure compliance

4. SUMMARIZE:
   - Generate document summaries
   - Extract key points
   - Maintain semantic meaning
   - Optimize for search

5. EMBED:
   - Generate document embeddings
   - Process text chunks
   - Create vector representations
   - Prepare for indexing

6. CLUSTER:
   - Group similar documents
   - Identify topics
   - Build document relationships
   - Optimize search results

7. INDEX:
   - Store documents in vector index
   - Update search indices
   - Maintain relationships
   - Enable efficient retrieval

Usage:
    ```python
    from pipeline.steps import PipelineStep

    # Select specific steps
    steps = {
        PipelineStep.LOAD,
        PipelineStep.SUMMARIZE,
        PipelineStep.INDEX
    }

    # Process documents with selected steps
    pipeline.process_documents(steps=steps)
    ```

Note:
    - Steps can be combined flexibly
    - Some steps depend on others
    - Steps can be skipped if not needed
    - Order is maintained by pipeline
"""

from enum import Enum, auto


class PipelineStep(Enum):
    """Enum defining the available pipeline processing steps.

    Each step represents a distinct phase of document processing:
    - LOAD: Document loading and initial parsing
    - DEDUPLICATE: Duplicate detection and removal
    - PII: Personally identifiable information detection
    - SUMMARIZE: Document summarization
    - EMBED: Vector embedding generation
    - CLUSTER: Document clustering and topic detection
    - INDEX: Vector index storage and updates
    """

    LOAD = auto()
    DEDUPLICATE = auto()
    PII = auto()
    SUMMARIZE = auto()
    EMBED = auto()
    CLUSTER = auto()
    INDEX = auto()

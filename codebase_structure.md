.
├── README.md
├── codebase_structure.md
├── communication_schema.json
├── custom_logs
│   └── pipeline.json
├── logs
│   └── pipeline.json
├── notion_project.egg-info
│   ├── PKG-INFO
│   ├── SOURCES.txt
│   ├── dependency_links.txt
│   └── top_level.txt
├── pytest.ini
├── query_examples.md
├── refactoring_proposal.md
├── requirements.txt
├── run_pipeline.py
├── setup.py
├── src
│   ├── __pycache__
│   │   └── main.cpython-311.pyc
│   ├── configuration
│   │   ├── __pycache__
│   │   │   └── logger_setup.cpython-311.pyc
│   │   └── logger_setup.py
│   ├── connectors
│   │   ├── __pycache__
│   │   │   └── notion_connector.cpython-311.pyc
│   │   └── notion_connector.py
│   ├── embeddings
│   │   ├── __pycache__
│   │   │   └── embedding_generator.cpython-311.pyc
│   │   └── embedding_generator.py
│   ├── indexing
│   │   ├── __pycache__
│   │   │   ├── document_manager.cpython-311.pyc
│   │   │   ├── schema_manager.cpython-311.pyc
│   │   │   ├── search_manager.cpython-311.pyc
│   │   │   └── vector_index.cpython-311.pyc
│   │   ├── document
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-311.pyc
│   │   │   │   ├── batch_manager.cpython-311.pyc
│   │   │   │   ├── document_processor.cpython-311.pyc
│   │   │   │   └── document_storage.cpython-311.pyc
│   │   │   ├── batch_manager.py
│   │   │   ├── document_processor.py
│   │   │   └── document_storage.py
│   │   ├── document_manager.py
│   │   ├── index
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-311.pyc
│   │   │   │   ├── index_config.cpython-311.pyc
│   │   │   │   ├── index_operations.cpython-311.pyc
│   │   │   │   └── vector_index.cpython-311.pyc
│   │   │   ├── index_config.py
│   │   │   ├── index_operations.py
│   │   │   └── vector_index.py
│   │   ├── schema
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-311.pyc
│   │   │   │   ├── schema_definition.cpython-311.pyc
│   │   │   │   ├── schema_migrator.cpython-311.pyc
│   │   │   │   └── schema_validator.cpython-311.pyc
│   │   │   ├── schema_definition.py
│   │   │   ├── schema_migrator.py
│   │   │   └── schema_validator.py
│   │   ├── schema_manager.py
│   │   ├── search
│   │   │   ├── __init__.py
│   │   │   ├── __pycache__
│   │   │   │   ├── __init__.cpython-311.pyc
│   │   │   │   ├── query_builder.cpython-311.pyc
│   │   │   │   ├── search_executor.cpython-311.pyc
│   │   │   │   └── search_result.cpython-311.pyc
│   │   │   ├── query_builder.py
│   │   │   ├── search_executor.py
│   │   │   └── search_result.py
│   │   ├── search_manager.py
│   │   └── vector_index.py
│   ├── main.py
│   ├── pipeline
│   │   ├── __init__.py
│   │   ├── __pycache__
│   │   │   ├── __init__.cpython-311.pyc
│   │   │   ├── core.cpython-311.pyc
│   │   │   ├── document_ops.cpython-311.pyc
│   │   │   ├── search.cpython-311.pyc
│   │   │   └── steps.cpython-311.pyc
│   │   ├── core.py
│   │   ├── document_ops.py
│   │   ├── search.py
│   │   └── steps.py
│   └── utils
│       ├── __pycache__
│       │   ├── cache_manager.cpython-311.pyc
│       │   ├── document_processing.cpython-311.pyc
│       │   ├── monitoring.cpython-311.pyc
│       │   ├── pii_detector.cpython-311.pyc
│       │   ├── summarizer.cpython-311.pyc
│       │   ├── text_processing.cpython-311.pyc
│       │   └── topic_clustering.cpython-311.pyc
│       ├── cache_manager.py
│       ├── document_processing.py
│       ├── monitoring.py
│       ├── pii_detector.py
│       ├── summarizer.py
│       ├── text_processing.py
│       └── topic_clustering.py
├── system_analysis.md
├── test_failures.txt
└── tests
    ├── README.md
    ├── __pycache__
    │   └── conftest.cpython-311-pytest-7.4.0.pyc
    ├── conftest.py
    ├── data
    │   └── sample_documents.json
    ├── fixtures
    │   ├── __init__.py
    │   ├── __pycache__
    │   │   ├── __init__.cpython-311.pyc
    │   │   ├── components.cpython-311.pyc
    │   │   ├── documents.cpython-311.pyc
    │   │   ├── errors.cpython-311.pyc
    │   │   └── pipeline.cpython-311.pyc
    │   ├── components.py
    │   ├── documents.py
    │   ├── errors.py
    │   └── pipeline.py
    └── unit
        ├── __pycache__
        │   └── test_main.cpython-311-pytest-7.4.0.pyc
        ├── configuration
        │   ├── __pycache__
        │   │   └── test_logger_setup.cpython-311-pytest-7.4.0.pyc
        │   └── test_logger_setup.py
        ├── connectors
        │   ├── __pycache__
        │   │   └── test_notion_connector.cpython-311-pytest-7.4.0.pyc
        │   └── test_notion_connector.py
        ├── embeddings
        │   ├── __pycache__
        │   │   └── test_embedding_generator.cpython-311-pytest-7.4.0.pyc
        │   └── test_embedding_generator.py
        ├── indexing
        │   ├── __pycache__
        │   │   └── test_vector_index.cpython-311-pytest-7.4.0.pyc
        │   └── test_vector_index.py
        ├── pipeline
        │   ├── __pycache__
        │   │   ├── test_core.cpython-311-pytest-7.4.0.pyc
        │   │   ├── test_document_ops.cpython-311-pytest-7.4.0.pyc
        │   │   ├── test_search.cpython-311-pytest-7.4.0.pyc
        │   │   └── test_steps.cpython-311-pytest-7.4.0.pyc
        │   ├── test_core.py
        │   ├── test_document_ops.py
        │   ├── test_search.py
        │   └── test_steps.py
        ├── test_main.py
        └── utils
            ├── __pycache__
            │   ├── test_cache_manager.cpython-311-pytest-7.4.0.pyc
            │   ├── test_document_processing.cpython-311-pytest-7.4.0.pyc
            │   ├── test_monitoring.cpython-311-pytest-7.4.0.pyc
            │   ├── test_pii_detector.cpython-311-pytest-7.4.0.pyc
            │   ├── test_summarizer.cpython-311-pytest-7.4.0.pyc
            │   ├── test_text_processing.cpython-311-pytest-7.4.0.pyc
            │   └── test_topic_clustering.cpython-311-pytest-7.4.0.pyc
            ├── test_cache_manager.py
            ├── test_document_processing.py
            ├── test_monitoring.py
            ├── test_pii_detector.py
            ├── test_summarizer.py
            ├── test_text_processing.py
            └── test_topic_clustering.py

45 directories, 135 files

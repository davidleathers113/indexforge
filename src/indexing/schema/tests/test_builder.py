"""
Tests for the SchemaBuilder class.

This module contains tests for schema construction using the SchemaBuilder.
"""

import pytest

from src.indexing.schema.builder import SchemaBuilder
from src.indexing.schema.exceptions import ClassNameError


def test_schema_builder_initialization():
    """Test SchemaBuilder initialization with valid class name."""
    builder = SchemaBuilder("Document")
    assert builder.class_name == "Document"
    assert len(builder.properties) == 1  # schema_version property
    assert builder.properties[0]["name"] == "schema_version"


def test_schema_builder_invalid_class_name():
    """Test SchemaBuilder initialization with invalid class name."""
    with pytest.raises(ClassNameError):
        SchemaBuilder("")

    with pytest.raises(ClassNameError):
        SchemaBuilder("123")

    with pytest.raises(ClassNameError):
        SchemaBuilder("lowercase")


def test_add_text_property():
    """Test adding text properties."""
    builder = SchemaBuilder("Document")
    builder.add_text_property(
        "content",
        description="Document content",
        moduleConfig={
            "text2vec-transformers": {
                "skip": False,
                "tokenization": "word",
            }
        },
        indexInverted=True,
    )

    props = builder.properties
    text_prop = next(p for p in props if p["name"] == "content")
    assert text_prop["dataType"] == ["text"]
    assert text_prop["description"] == "Document content"
    assert text_prop["moduleConfig"]["text2vec-transformers"]["tokenization"] == "word"
    assert text_prop["indexInverted"] is True


def test_add_vector_property():
    """Test adding vector properties."""
    builder = SchemaBuilder("Document")
    builder.add_vector_property(
        "embedding",
        vectorIndexConfig={"dimensions": 768},
        description="Document embedding",
    )

    props = builder.properties
    vector_prop = next(p for p in props if p["name"] == "embedding")
    assert vector_prop["dataType"] == ["vector"]
    assert vector_prop["description"] == "Document embedding"
    assert vector_prop["vectorIndexConfig"]["dimensions"] == 768


def test_add_reference_property():
    """Test adding reference properties."""
    builder = SchemaBuilder("Document")
    builder.add_reference_property(
        "parent",
        "Document",
        description="Parent document reference",
    )

    props = builder.properties
    ref_prop = next(p for p in props if p["name"] == "parent")
    assert ref_prop["dataType"] == ["cross-reference"]
    assert ref_prop["description"] == "Parent document reference"
    assert ref_prop["crossReference"]["target"] == ["Document"]


def test_add_int_property():
    """Test adding integer properties."""
    builder = SchemaBuilder("Document")
    builder.add_int_property(
        "version",
        description="Document version",
        defaultValue=1,
        indexInverted=True,
    )

    props = builder.properties
    int_prop = next(p for p in props if p["name"] == "version")
    assert int_prop["dataType"] == ["int"]
    assert int_prop["description"] == "Document version"
    assert int_prop["defaultValue"] == 1
    assert int_prop["indexInverted"] is True


def test_with_vectorizer():
    """Test vectorizer configuration."""
    builder = SchemaBuilder("Document")
    builder.with_vectorizer(
        "text2vec-transformers",
        model="sentence-transformers/all-mpnet-base-v2",
        pooling="masked_mean",
    )

    config = builder.vectorizer_config
    assert config["vectorizer"] == "text2vec-transformers"
    assert (
        config["moduleConfig"]["text2vec-transformers"]["model"]
        == "sentence-transformers/all-mpnet-base-v2"
    )
    assert config["moduleConfig"]["text2vec-transformers"]["poolingStrategy"] == "masked_mean"


def test_with_vector_index():
    """Test vector index configuration."""
    builder = SchemaBuilder("Document")
    builder.with_vector_index(
        distance="cosine",
        ef=200,
        maxConnections=128,
        dynamicEfFactor=8,
    )

    config = builder.vector_index_config
    assert config["distance"] == "cosine"
    assert config["ef"] == 200
    assert config["maxConnections"] == 128
    assert config["dynamicEfFactor"] == 8


def test_with_bm25():
    """Test BM25 configuration."""
    builder = SchemaBuilder("Document")
    builder.with_bm25(b=0.8, k1=1.5)

    config = builder.inverted_index_config
    assert config["bm25"]["b"] == 0.8
    assert config["bm25"]["k1"] == 1.5


def test_build_complete_schema():
    """Test building a complete schema."""
    builder = SchemaBuilder("Document")
    schema = (
        builder.add_text_property(
            "title",
            description="Document title",
            moduleConfig={"text2vec-transformers": {"skip": False}},
        )
        .add_vector_property(
            "embedding",
            vectorIndexConfig={"dimensions": 768},
        )
        .with_vectorizer("text2vec-transformers")
        .with_vector_index(distance="cosine", ef=100)
        .with_bm25(b=0.75, k1=1.2)
        .build()
    )

    assert schema["class"] == "Document"
    assert len(schema["properties"]) == 3  # schema_version + title + embedding
    assert schema["vectorizer"] == "text2vec-transformers"
    assert schema["vectorIndexConfig"]["distance"] == "cosine"
    assert schema["invertedIndexConfig"]["bm25"]["b"] == 0.75

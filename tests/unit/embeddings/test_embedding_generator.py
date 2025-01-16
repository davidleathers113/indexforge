"""Tests for the EmbeddingGenerator class."""
import numpy as np
from openai.types.create_embedding_response import CreateEmbeddingResponse
from openai.types.embedding import Embedding
import pytest

from src.embeddings.embedding_generator import EmbeddingGenerator
from src.utils.text_processing import ChunkingConfig


@pytest.fixture
def mock_openai():
    """Create a mock OpenAI client."""

    class MockOpenAI:

        def __init__(self):
            self.embeddings = self.MockEmbeddings(self)
            self.error_mode = False
            self.side_effect = None

        def raise_error(self):
            self.error_mode = True

        def close(self):
            pass

        class MockEmbeddings:

            def __init__(self, parent):
                self.parent = parent
                self.call_count = 0

            def create(self, model, input, dimensions=None, encoding_format=None):
                self.call_count += 1
                if self.parent.error_mode:
                    raise Exception('API Error')
                if self.parent.side_effect:
                    if isinstance(self.parent.side_effect, list):
                        response = self.parent.side_effect.pop(0)
                        return response
                    return self.parent.side_effect
                if isinstance(input, str):
                    return CreateEmbeddingResponse(data=[Embedding(embedding=[0.1, 0.2, 0.3], index=0, object='embedding')], model=model, object='list', usage={'prompt_tokens': 4, 'total_tokens': 4})
                else:
                    raise ValueError('Invalid input type')
    return MockOpenAI()


@pytest.fixture
def sample_document():
    """Create a sample document for testing."""
    return {'content': {'body': 'This is a test document.', 'summary': 'Test summary'}, 'embeddings': {'body': None, 'summary': None, 'version': None, 'model': None}, 'metadata': {'title': 'Test Document'}}


@pytest.fixture
def embedding_generator(mock_openai):
    """Create an EmbeddingGenerator instance with mocks."""
    return EmbeddingGenerator(model='text-embedding-3-small', chunk_size=256, chunk_overlap=50, dimensions=3, client=mock_openai)


def test_embedding_generator_initialization(mock_openai):
    """Test EmbeddingGenerator initialization with default values."""
    generator = EmbeddingGenerator(client=mock_openai)
    assert generator.model == 'text-embedding-3-small'
    assert isinstance(generator.chunking_config, ChunkingConfig)
    assert generator.chunking_config.chunk_size == 512
    assert generator.chunking_config.chunk_overlap == 50
    assert generator.dimensions is None
    assert generator.client == mock_openai


def test_embedding_generator_custom_config(mock_openai):
    """Test EmbeddingGenerator initialization with custom values."""
    generator = EmbeddingGenerator(model='custom-model', chunk_size=128, chunk_overlap=25, dimensions=128, client=mock_openai)
    assert generator.model == 'custom-model'
    assert generator.chunking_config.chunk_size == 128
    assert generator.chunking_config.chunk_overlap == 25
    assert generator.dimensions == 128
    assert generator.client == mock_openai
    assert generator.chunking_config.max_chunk_size == 128 * 4


def test_get_embedding(embedding_generator, mock_openai):
    """Test generating embedding for single text."""
    text = 'Test text'
    embedding = embedding_generator._get_embedding(text)
    assert isinstance(embedding, list)
    assert len(embedding) == 3
    assert mock_openai.embeddings.call_count == 1
    expected = [0.267261, 0.534522, 0.801784]
    np.testing.assert_array_almost_equal(embedding, expected, decimal=5)


def test_get_embedding_normalization(embedding_generator):
    """Test L2 normalization of embeddings."""
    vec = [1.0, 2.0, 2.0]
    normalized = embedding_generator._normalize_l2(vec)
    assert np.allclose(np.linalg.norm(normalized), 1.0)
    expected = np.array([0.333333, 0.666667, 0.666667])
    assert np.allclose(normalized, expected, rtol=0.001)
    matrix = [[1.0, 2.0, 2.0], [3.0, 4.0, 4.0]]
    normalized = embedding_generator._normalize_l2(matrix)
    assert all(np.allclose(np.linalg.norm(row), 1.0) for row in normalized)
    expected = np.array([[0.33333333, 0.66666667, 0.66666667], [0.46852129, 0.62469505, 0.62469505]])
    assert np.allclose(normalized, expected, rtol=0.001)


def test_get_embedding_error_handling(embedding_generator, mock_openai):
    """Test error handling in embedding generation."""
    mock_openai.raise_error()
    with pytest.raises(Exception, match='Error generating embedding: API Error'):
        embedding_generator._get_embedding('Test text')
    assert mock_openai.embeddings.call_count == 1
    mock_openai.error_mode = False
    with pytest.raises(Exception, match='Error generating embedding: Invalid input type: text must be a string'):
        embedding_generator._get_embedding(None)


def test_generate_embeddings_single_document(embedding_generator, sample_document):
    """Test generating embeddings for a single document."""
    docs = embedding_generator.generate_embeddings([sample_document])
    assert len(docs) == 1
    doc = docs[0]
    assert isinstance(doc['embeddings']['body'], list)
    assert len(doc['embeddings']['body']) == 3
    assert doc['embeddings']['version'] == 'v1'
    assert doc['embeddings']['model'] == embedding_generator.model


def test_generate_embeddings_long_document(embedding_generator, mock_openai):
    """Test generating embeddings for document requiring chunking."""
    long_doc = {'content': {'body': 'test. ' * 1000, 'summary': 'Test summary'}, 'embeddings': {'body': None, 'summary': None, 'version': None, 'model': None}, 'metadata': {'title': 'Long Document'}}
    docs = embedding_generator.generate_embeddings([long_doc])
    assert len(docs) == 1
    doc = docs[0]
    assert isinstance(doc['embeddings']['body'], list)
    assert len(doc['embeddings']['body']) == 3
    assert doc['embeddings']['chunks'] is not None
    assert isinstance(doc['embeddings']['chunks']['texts'], list)
    assert isinstance(doc['embeddings']['chunks']['vectors'], list)


def test_generate_embeddings_batch(embedding_generator, sample_document):
    """Test generating embeddings for multiple documents."""
    docs = [dict(sample_document), dict(sample_document)]
    processed_docs = embedding_generator.generate_embeddings(docs)
    assert len(processed_docs) == 2
    for doc in processed_docs:
        assert doc['embeddings']['version'] == 'v1'
        assert doc['embeddings']['model'] == embedding_generator.model
        assert isinstance(doc['embeddings']['body'], list)
        assert len(doc['embeddings']['body']) == 3


def test_generate_embeddings_api_error(embedding_generator, mock_openai, sample_document):
    """Test handling of API errors during embedding generation."""
    mock_openai.raise_error()
    docs = embedding_generator.generate_embeddings([dict(sample_document)])
    assert len(docs) == 1
    assert docs[0]['embeddings']['version'] == 'v1_failed'
    assert docs[0]['embeddings']['body'] == []
    assert 'error' in docs[0]['embeddings']
    assert 'Failed to generate embeddings for all chunks' in docs[0]['embeddings']['error']


def test_generate_embeddings_invalid_document(embedding_generator):
    """Test handling of invalid document structure."""
    invalid_doc = {'content': {}, 'embeddings': {'body': None, 'summary': None, 'version': None, 'model': None}}
    docs = embedding_generator.generate_embeddings([invalid_doc])
    assert len(docs) == 1
    assert docs[0]['embeddings']['version'] == 'v1_failed'
    assert 'Document has no body text' in docs[0]['embeddings']['error']


def test_chunk_averaging(embedding_generator, mock_openai):
    """Test averaging of chunk embeddings."""
    mock_openai.side_effect = [CreateEmbeddingResponse(data=[Embedding(embedding=[0.1, 0.2, 0.3], index=0, object='embedding')], model='text-embedding-3-small', object='list', usage={'prompt_tokens': 4, 'total_tokens': 4}), CreateEmbeddingResponse(data=[Embedding(embedding=[0.4, 0.5, 0.6], index=0, object='embedding')], model='text-embedding-3-small', object='list', usage={'prompt_tokens': 4, 'total_tokens': 4})]
    doc = {'content': {'body': 'chunk1. ' * 500 + 'chunk2. ' * 500, 'summary': None}, 'embeddings': {'body': None, 'summary': None, 'version': None, 'model': None}, 'metadata': {'title': 'Test'}}
    docs = embedding_generator.generate_embeddings([doc])
    expected_avg = [0.274, 0.536, 0.798]
    np.testing.assert_array_almost_equal(docs[0]['embeddings']['body'], expected_avg, decimal=2)
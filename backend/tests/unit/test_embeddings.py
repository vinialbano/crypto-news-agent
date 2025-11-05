"""Unit tests for embeddings service."""
import pytest
from unittest.mock import Mock, AsyncMock, patch
import numpy as np

from app.services.embeddings import EmbeddingsService


@pytest.fixture
def mock_ollama_embeddings():
    """Mock OllamaEmbeddings instance for testing."""
    mock_instance = Mock()
    return mock_instance


@pytest.fixture
def embeddings_service(mock_ollama_embeddings):
    """Create EmbeddingsService with mocked Ollama."""
    return EmbeddingsService(embeddings=mock_ollama_embeddings)


def test_embed_query_returns_correct_dimension(embeddings_service, mock_ollama_embeddings):
    """Test that embed_query returns 768-dimensional vector."""
    # Mock the response
    mock_ollama_embeddings.embed_query.return_value = np.random.rand(768).tolist()

    result = embeddings_service.embed_query("What happened to Bitcoin today?")

    assert isinstance(result, list)
    assert len(result) == 768
    assert all(isinstance(x, float) for x in result)


def test_embed_query_calls_ollama(embeddings_service, mock_ollama_embeddings):
    """Test that embed_query calls Ollama with correct query."""
    mock_ollama_embeddings.embed_query.return_value = [0.1] * 768

    query = "What is the price of Ethereum?"
    embeddings_service.embed_query(query)

    mock_ollama_embeddings.embed_query.assert_called_once_with(query)


def test_embed_documents_returns_list_of_vectors(embeddings_service, mock_ollama_embeddings):
    """Test that embed_documents returns list of 768-dimensional vectors."""
    documents = [
        "Bitcoin surged to new high",
        "Ethereum price increased",
        "Crypto market bullish"
    ]

    # Mock the response
    mock_ollama_embeddings.embed_documents.return_value = [
        np.random.rand(768).tolist() for _ in documents
    ]

    result = embeddings_service.embed_documents(documents)

    assert isinstance(result, list)
    assert len(result) == 3
    assert all(len(vec) == 768 for vec in result)
    assert all(isinstance(x, float) for vec in result for x in vec)


def test_embed_documents_calls_ollama(embeddings_service, mock_ollama_embeddings):
    """Test that embed_documents calls Ollama with correct documents."""
    documents = ["Doc 1", "Doc 2"]
    mock_ollama_embeddings.embed_documents.return_value = [[0.1] * 768, [0.2] * 768]

    embeddings_service.embed_documents(documents)

    mock_ollama_embeddings.embed_documents.assert_called_once_with(documents)


def test_embed_empty_query_raises_error(embeddings_service):
    """Test that embedding empty query raises ValueError."""
    with pytest.raises(ValueError, match="Query cannot be empty"):
        embeddings_service.embed_query("")


def test_embed_empty_documents_list_raises_error(embeddings_service):
    """Test that embedding empty documents list raises ValueError."""
    with pytest.raises(ValueError, match="Documents list cannot be empty"):
        embeddings_service.embed_documents([])


def test_embed_query_with_special_characters(embeddings_service, mock_ollama_embeddings):
    """Test embedding query with special characters."""
    mock_ollama_embeddings.embed_query.return_value = [0.1] * 768

    query = "What is Bitcoin's price? It's $100k!"
    result = embeddings_service.embed_query(query)

    assert len(result) == 768
    mock_ollama_embeddings.embed_query.assert_called_once_with(query)


def test_embed_documents_handles_long_text(embeddings_service, mock_ollama_embeddings):
    """Test embedding documents with long text content."""
    long_text = "Bitcoin " * 1000  # Very long document
    mock_ollama_embeddings.embed_documents.return_value = [[0.1] * 768]

    result = embeddings_service.embed_documents([long_text])

    assert len(result) == 1
    assert len(result[0]) == 768


@pytest.mark.asyncio
async def test_embed_query_async(embeddings_service, mock_ollama_embeddings):
    """Test async version of embed_query if implemented."""
    mock_ollama_embeddings.aembed_query = AsyncMock(return_value=[0.1] * 768)

    if hasattr(embeddings_service, 'aembed_query'):
        result = await embeddings_service.aembed_query("What is Bitcoin?")
        assert len(result) == 768
    else:
        pytest.skip("Async embed_query not implemented")


def test_embeddings_service_initialization():
    """Test EmbeddingsService initializes with dependency injection."""
    from langchain_ollama import OllamaEmbeddings

    # Test that create_embeddings_service factory works
    from app.services.embeddings import create_embeddings_service

    service = create_embeddings_service(
        base_url="http://localhost:11434",
        model="nomic-embed-text"
    )

    assert service is not None
    assert hasattr(service, '_embeddings')


def test_embeddings_service_connection_error(embeddings_service, mock_ollama_embeddings):
    """Test handling of connection errors to Ollama service."""
    mock_ollama_embeddings.embed_query.side_effect = ConnectionError("Ollama service unavailable")

    with pytest.raises(ConnectionError, match="Ollama service unavailable"):
        embeddings_service.embed_query("What is Bitcoin?")


def test_embed_documents_with_mixed_length_texts(embeddings_service, mock_ollama_embeddings):
    """Test embedding documents of varying lengths."""
    documents = [
        "Short",
        "Medium length document about crypto",
        "Very long document " * 100
    ]

    mock_ollama_embeddings.embed_documents.return_value = [
        [0.1] * 768,
        [0.2] * 768,
        [0.3] * 768
    ]

    result = embeddings_service.embed_documents(documents)

    assert len(result) == 3
    assert all(len(vec) == 768 for vec in result)

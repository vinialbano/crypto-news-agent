"""Unit tests for embeddings service."""

from unittest.mock import AsyncMock, Mock

import numpy as np
import pytest

from app.services.embeddings import EmbeddingsService


@pytest.fixture
def mock_ollama_embeddings():
    return Mock()


@pytest.fixture
def embeddings_service(mock_ollama_embeddings):
    return EmbeddingsService(embeddings=mock_ollama_embeddings)


def test_embed_query_returns_correct_dimension(
    embeddings_service, mock_ollama_embeddings
):
    mock_ollama_embeddings.embed_query.return_value = np.random.rand(768).tolist()

    result = embeddings_service.embed_query("What happened to Bitcoin today?")

    assert isinstance(result, list)
    assert len(result) == 768
    assert all(isinstance(x, float) for x in result)


def test_embed_query_calls_ollama(embeddings_service, mock_ollama_embeddings):
    mock_ollama_embeddings.embed_query.return_value = [0.1] * 768

    query = "What is the price of Ethereum?"
    embeddings_service.embed_query(query)

    mock_ollama_embeddings.embed_query.assert_called_once_with(query)


def test_embed_documents_returns_list_of_vectors(
    embeddings_service, mock_ollama_embeddings
):
    documents = [
        "Bitcoin surged to new high",
        "Ethereum price increased",
        "Crypto market bullish",
    ]

    mock_ollama_embeddings.embed_documents.return_value = [
        np.random.rand(768).tolist() for _ in documents
    ]

    result = embeddings_service.embed_documents(documents)

    assert isinstance(result, list)
    assert len(result) == 3
    assert all(len(vec) == 768 for vec in result)
    assert all(isinstance(x, float) for vec in result for x in vec)


def test_embed_documents_calls_ollama(embeddings_service, mock_ollama_embeddings):
    documents = ["Doc 1", "Doc 2"]
    mock_ollama_embeddings.embed_documents.return_value = [[0.1] * 768, [0.2] * 768]

    embeddings_service.embed_documents(documents)

    mock_ollama_embeddings.embed_documents.assert_called_once_with(documents)


def test_embed_empty_query_raises_error(embeddings_service):
    with pytest.raises(ValueError, match="Query cannot be empty"):
        embeddings_service.embed_query("")


def test_embed_empty_documents_list_raises_error(embeddings_service):
    with pytest.raises(ValueError, match="Documents list cannot be empty"):
        embeddings_service.embed_documents([])


def test_embed_query_with_special_characters(
    embeddings_service, mock_ollama_embeddings
):
    mock_ollama_embeddings.embed_query.return_value = [0.1] * 768

    query = "What is Bitcoin's price? It's $100k!"
    result = embeddings_service.embed_query(query)

    assert len(result) == 768
    mock_ollama_embeddings.embed_query.assert_called_once_with(query)


def test_embed_documents_handles_long_text(embeddings_service, mock_ollama_embeddings):
    long_text = "Bitcoin " * 1000
    mock_ollama_embeddings.embed_documents.return_value = [[0.1] * 768]

    result = embeddings_service.embed_documents([long_text])

    assert len(result) == 1
    assert len(result[0]) == 768


@pytest.mark.asyncio
async def test_embed_query_async(embeddings_service, mock_ollama_embeddings):
    mock_ollama_embeddings.aembed_query = AsyncMock(return_value=[0.1] * 768)

    if hasattr(embeddings_service, "aembed_query"):
        result = await embeddings_service.aembed_query("What is Bitcoin?")
        assert len(result) == 768
    else:
        pytest.skip("Async embed_query not implemented")


def test_embeddings_service_connection_error(
    embeddings_service, mock_ollama_embeddings
):
    from app.exceptions import EmbeddingGenerationError

    mock_ollama_embeddings.embed_query.side_effect = ConnectionError(
        "Ollama service unavailable"
    )

    with pytest.raises(EmbeddingGenerationError, match="Failed to generate embedding"):
        embeddings_service.embed_query("What is Bitcoin?")


def test_embed_documents_with_mixed_length_texts(
    embeddings_service, mock_ollama_embeddings
):
    documents = [
        "Short",
        "Medium length document about crypto",
        "Very long document " * 100,
    ]

    mock_ollama_embeddings.embed_documents.return_value = [
        [0.1] * 768,
        [0.2] * 768,
        [0.3] * 768,
    ]

    result = embeddings_service.embed_documents(documents)

    assert len(result) == 3
    assert all(len(vec) == 768 for vec in result)

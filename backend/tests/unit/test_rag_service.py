"""Unit tests for RAG service."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.features.news.models import NewsArticle
from app.features.questions.rag_service import RAGService


@pytest.fixture
def mock_embeddings_service():
    """Create mock embeddings service."""
    service = AsyncMock()
    service.aembed_query.return_value = [0.1] * 768  # Mock embedding vector
    return service


@pytest.fixture
def mock_chat_model():
    """Create mock chat model."""
    model = AsyncMock()
    return model


@pytest.fixture
def mock_repository():
    """Create mock news repository."""
    repository = MagicMock()
    return repository


@pytest.fixture
def rag_service(mock_embeddings_service, mock_chat_model, mock_repository):
    """Create RAG service instance with dependency injection."""
    return RAGService(
        embeddings_service=mock_embeddings_service,
        chat_model=mock_chat_model,
        repository=mock_repository,
    )


@pytest.fixture
def sample_articles():
    """Create sample articles for testing."""
    return [
        NewsArticle(
            id=1,
            title="Bitcoin hits $100k",
            url="https://example.com/1",
            content="Bitcoin has reached $100,000 for the first time ever. The cryptocurrency market is celebrating this historic milestone. Analysts predict further growth in the coming months.",
            source_name="Crypto News",
            content_hash="hash1",
            embedding=[0.1] * 768,
        ),
        NewsArticle(
            id=2,
            title="Ethereum upgrade successful",
            url="https://example.com/2",
            content="The Ethereum network has successfully completed its latest upgrade. The update brings improved scalability and reduced gas fees. Developers are optimistic about the future.",
            source_name="DeFi Today",
            content_hash="hash2",
            embedding=[0.2] * 768,
        ),
        NewsArticle(
            id=3,
            title="Crypto regulations announced",
            url="https://example.com/3",
            content="New cryptocurrency regulations have been announced by the SEC. The rules aim to protect investors while fostering innovation. Industry leaders have mixed reactions to the announcement.",
            source_name="Regulatory Watch",
            content_hash="hash3",
            embedding=[0.3] * 768,
        ),
    ]


class TestRAGService:
    """Test cases for RAGService."""

    @pytest.mark.asyncio
    async def test_stream_answer_success(self, rag_service, sample_articles):
        """Test successful answer streaming."""
        # Setup mocks - repository is already injected via fixture
        rag_service.repository.semantic_search.return_value = [
            (sample_articles[0], 0.1),
            (sample_articles[1], 0.15),
            (sample_articles[2], 0.2),
        ]

        # Mock chat model streaming
        mock_chunk1 = MagicMock()
        mock_chunk1.content = "Bitcoin"
        mock_chunk2 = MagicMock()
        mock_chunk2.content = " has reached"
        mock_chunk3 = MagicMock()
        mock_chunk3.content = " $100k."

        async def mock_astream(prompt):
            for chunk in [mock_chunk1, mock_chunk2, mock_chunk3]:
                yield chunk

        rag_service.chat_model.astream = mock_astream

        # Stream answer
        question = "What is the Bitcoin price?"
        messages = []
        async for message in rag_service.stream_answer(question):
            messages.append(message)

        # Assertions
        assert len(messages) > 0

        # Check sources message
        sources_msg = messages[0]
        assert sources_msg["type"] == "sources"
        assert sources_msg["count"] == 3
        assert len(sources_msg["sources"]) == 3
        assert sources_msg["sources"][0]["title"] == "Bitcoin hits $100k"

        # Check content chunks
        content_msgs = [m for m in messages if m["type"] == "chunk"]
        assert len(content_msgs) == 3
        full_content = "".join(m["content"] for m in content_msgs)
        assert full_content == "Bitcoin has reached $100k."

        # Check done message
        done_msg = messages[-1]
        assert done_msg["type"] == "done"

    @pytest.mark.asyncio
    async def test_stream_answer_no_relevant_articles(self, rag_service):
        """Test answer streaming when no relevant articles found."""
        # Setup mocks - distance too high (not relevant)
        mock_article = MagicMock()
        rag_service.repository.semantic_search.return_value = [(mock_article, 0.9)]

        # Stream answer
        question = "What is the price of XYZ token?"
        messages = []
        async for message in rag_service.stream_answer(question):
            messages.append(message)

        # Assertions
        assert len(messages) == 1
        assert messages[0]["type"] == "error"
        assert "don't have enough information" in messages[0]["content"]

    @pytest.mark.asyncio
    async def test_stream_answer_empty_results(self, rag_service):
        """Test answer streaming when search returns empty."""
        # Setup mocks
        rag_service.repository.semantic_search.return_value = []

        # Stream answer
        question = "Tell me about crypto"
        messages = []
        async for message in rag_service.stream_answer(question):
            messages.append(message)

        # Assertions
        assert len(messages) == 1
        assert messages[0]["type"] == "error"

    @pytest.mark.asyncio
    async def test_stream_answer_exception_handling(self, rag_service):
        """Test answer streaming handles exceptions."""
        import pytest
        from app.shared.exceptions import RAGError

        # Setup mocks to raise exception
        rag_service.repository.semantic_search.side_effect = Exception("Database error")

        # Stream answer should raise RAGError
        question = "What is happening?"
        with pytest.raises(RAGError, match="Failed to generate answer"):
            async for message in rag_service.stream_answer(question):
                pass

    def test_build_context(self, rag_service, sample_articles):
        """Test context building from articles."""
        context = rag_service._build_context(sample_articles)

        # Assertions
        assert "Bitcoin hits $100k" in context
        assert "Ethereum upgrade successful" in context
        assert "Crypto regulations announced" in context
        assert "Crypto News" in context
        assert "DeFi Today" in context
        assert "Regulatory Watch" in context

        # Check article content is included
        assert "reached $100,000" in context
        assert "successfully completed" in context
        assert "announced by the SEC" in context

    def test_build_context_truncation(self, rag_service, sample_articles):
        """Test context respects max token limit."""
        # Create article with very long content
        long_article = NewsArticle(
            id=4,
            title="Very long article",
            url="https://example.com/4",
            content="A" * 10000,  # Very long content
            source_name="Test Source",
            content_hash="hash4",
            embedding=[0.4] * 768,
        )

        context = rag_service._build_context([long_article])

        # Context should be limited (rough estimate: 4 chars per token)
        # With MAX_CONTEXT_TOKENS=2000, should be around 8000 chars max
        assert len(context) < 10000

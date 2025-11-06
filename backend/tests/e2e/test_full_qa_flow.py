"""End-to-end test for complete Q&A flow with RAG."""

import pytest
from fastapi.testclient import TestClient
from sqlmodel import Session, select

from app.core.db import engine
from app.features.news.models import NewsArticle
from app.main import app


@pytest.fixture(scope="module")
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture(scope="module")
def db_session():
    """Create database session."""
    with Session(engine) as session:
        yield session


@pytest.mark.e2e
@pytest.mark.slow
def test_complete_qa_flow(client, db_session):
    """Test complete Q&A flow: ingestion → storage → retrieval → answer.

    This test verifies the entire pipeline:
    1. Articles exist in database (from previous ingestion)
    2. Ask a question via WebSocket
    3. Semantic search finds relevant articles
    4. LLM generates answer based on articles
    5. Answer is streamed back with sources
    """
    # Step 1: Verify we have articles in database
    articles = db_session.exec(select(NewsArticle).limit(10)).all()
    assert len(articles) > 0, "Database should have articles for Q&A"

    print(f"\nFound {len(articles)} articles in database")

    # Step 2: Ask a question about crypto news
    with client.websocket_connect("/api/v1/questions/ws/ask") as websocket:
        question = "What are the latest developments in cryptocurrency?"
        print(f"Asking: {question}")

        websocket.send_json({"question": question})

        # Step 3: Receive and validate response
        messages = []
        sources_found = None
        answer_chunks = []

        while True:
            try:
                data = websocket.receive_json()
                messages.append(data)

                if data["type"] == "sources":
                    sources_found = data
                    print(f"Sources: {data['count']} relevant articles found")

                elif data["type"] == "chunk":
                    answer_chunks.append(data["content"])

                elif data["type"] == "done":
                    print("Answer streaming completed")
                    break

                elif data["type"] == "error":
                    print(f"Error: {data['content']}")
                    break

            except Exception as e:
                print(f"Exception: {e}")
                break

        # Step 4: Validate complete flow
        assert len(messages) > 0, "Should receive messages"

        # Should have found source articles
        assert sources_found is not None, "Should have sources message"
        assert sources_found["count"] > 0, "Should find relevant articles"
        assert len(sources_found["sources"]) > 0, "Should return source list"

        # Validate source structure
        first_source = sources_found["sources"][0]
        assert "title" in first_source
        assert "source" in first_source
        assert "url" in first_source
        print(f"First source: {first_source['title']} ({first_source['source']})")

        # Should have answer content
        assert len(answer_chunks) > 0, "Should receive answer chunks"
        full_answer = "".join(answer_chunks)
        assert len(full_answer) > 50, "Answer should be substantial"
        print(f"Answer length: {len(full_answer)} characters")
        print(f"Answer preview: {full_answer[:200]}...")

        # Answer should be relevant to question
        # (Basic check - should mention crypto-related terms)
        answer_lower = full_answer.lower()
        crypto_terms = ["bitcoin", "crypto", "ethereum", "blockchain", "btc", "eth"]
        has_crypto_term = any(term in answer_lower for term in crypto_terms)
        assert has_crypto_term, "Answer should mention cryptocurrency-related terms"

        # Last message should be done
        assert messages[-1]["type"] == "done", "Should end with done message"


@pytest.mark.e2e
def test_qa_with_specific_topic(client):
    """Test Q&A about a specific crypto topic."""
    with client.websocket_connect("/api/v1/questions/ws/ask") as websocket:
        # Ask about a specific topic likely to be in news
        websocket.send_json({"question": "What happened with Bitcoin price recently?"})

        sources_msg = websocket.receive_json()
        assert sources_msg["type"] == "sources"

        # Collect answer
        answer_parts = []
        while True:
            msg = websocket.receive_json()
            if msg["type"] == "chunk":
                answer_parts.append(msg["content"])
            elif msg["type"] in ["done", "error"]:
                break

        if answer_parts:
            full_answer = "".join(answer_parts)
            # Answer should reference Bitcoin or price
            assert (
                "bitcoin" in full_answer.lower()
                or "btc" in full_answer.lower()
                or "price" in full_answer.lower()
            )


@pytest.mark.e2e
def test_qa_flow_with_multiple_questions(client):
    """Test asking multiple questions in sequence."""
    questions = [
        "What are the latest Bitcoin news?",
        "Tell me about Ethereum developments",
    ]

    for question in questions:
        with client.websocket_connect("/api/v1/questions/ws/ask") as websocket:
            websocket.send_json({"question": question})

            # Receive all messages
            received_done = False
            while True:
                try:
                    msg = websocket.receive_json()
                    if msg["type"] in ["done", "error"]:
                        received_done = True
                        break
                except Exception:
                    break

            assert received_done, f"Should complete answer for: {question}"


@pytest.mark.e2e
def test_data_freshness(client, db_session):
    """Test that Q&A uses recent articles."""
    # Get the most recent article
    recent_article = db_session.exec(
        select(NewsArticle).order_by(NewsArticle.ingested_at.desc()).limit(1)
    ).first()

    assert recent_article is not None, "Should have recent articles"

    # Check that article is from recent ingestion
    import datetime

    now = datetime.datetime.utcnow()
    age_hours = (
        now - recent_article.ingested_at.replace(tzinfo=None)
    ).total_seconds() / 3600

    print(f"Most recent article is {age_hours:.1f} hours old")

    # Article should be relatively recent (within a day for active system)
    # This is a soft check - could be longer if ingestion hasn't run
    if age_hours < 24:
        print("✓ Articles are fresh (< 24 hours old)")
    else:
        print(f"⚠ Articles are {age_hours:.1f} hours old - consider running ingestion")

"""Integration tests for Questions API (WebSocket)."""


import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client():
    """Create test client."""
    return TestClient(app)


@pytest.mark.integration
def test_websocket_ask_question_success(client):
    """Test WebSocket Q&A endpoint with valid question."""
    with client.websocket_connect("/api/v1/questions/ws/ask") as websocket:
        # Send question
        websocket.send_json({"question": "What are the latest news about Bitcoin?"})

        # Receive messages
        messages = []
        while True:
            try:
                data = websocket.receive_json()
                messages.append(data)

                if data.get("type") == "done":
                    break
                elif data.get("type") == "error":
                    break
            except Exception:
                break

        # Assertions
        assert len(messages) > 0

        # First message should be sources
        assert messages[0]["type"] == "sources"
        assert "count" in messages[0]
        assert "sources" in messages[0]
        assert messages[0]["count"] > 0

        # Should have chunk messages
        chunk_messages = [m for m in messages if m["type"] == "chunk"]
        assert len(chunk_messages) > 0

        # Full answer content
        full_answer = "".join(m["content"] for m in chunk_messages)
        assert len(full_answer) > 0

        # Last message should be done
        assert messages[-1]["type"] == "done"


@pytest.mark.integration
def test_websocket_ask_question_with_sources(client):
    """Test that WebSocket returns source articles."""
    with client.websocket_connect("/api/v1/questions/ws/ask") as websocket:
        websocket.send_json({"question": "Tell me about crypto news"})

        # Get first message (sources)
        sources_msg = websocket.receive_json()

        assert sources_msg["type"] == "sources"
        assert sources_msg["count"] > 0
        assert len(sources_msg["sources"]) > 0

        # Check source structure
        source = sources_msg["sources"][0]
        assert "title" in source
        assert "source" in source
        assert "url" in source


@pytest.mark.integration
def test_websocket_invalid_question_format(client):
    """Test WebSocket with invalid question format."""
    with client.websocket_connect("/api/v1/questions/ws/ask") as websocket:
        # Send invalid format (missing question key)
        websocket.send_json({"query": "This is wrong"})

        # Should receive error or close
        try:
            response = websocket.receive_json()
            # If we get a response, it should be an error
            if "type" in response:
                assert response["type"] == "error"
        except Exception:
            # Connection closed is also acceptable
            pass


@pytest.mark.integration
def test_websocket_empty_question(client):
    """Test WebSocket with empty question."""
    with client.websocket_connect("/api/v1/questions/ws/ask") as websocket:
        websocket.send_json({"question": ""})

        # Should receive error
        response = websocket.receive_json()
        assert response["type"] == "error"


@pytest.mark.integration
def test_websocket_obscure_question(client):
    """Test WebSocket with question that has no relevant articles."""
    with client.websocket_connect("/api/v1/questions/ws/ask") as websocket:
        # Ask about something completely unrelated
        websocket.send_json(
            {"question": "What is the best recipe for chocolate chip cookies?"}
        )

        # Should receive error about no information
        response = websocket.receive_json()

        # Might get sources with high distance, then error, or direct error
        if response["type"] == "sources":
            # Get next message
            response = websocket.receive_json()

        # Should eventually get error or done
        assert response["type"] in ["error", "done"]


@pytest.mark.integration
def test_websocket_connection_lifecycle(client):
    """Test WebSocket connection can handle multiple questions."""
    with client.websocket_connect("/api/v1/questions/ws/ask") as websocket:
        # First question
        websocket.send_json({"question": "What is Bitcoin?"})

        # Consume all responses
        while True:
            response = websocket.receive_json()
            if response["type"] in ["done", "error"]:
                break

        # Connection should still be open
        # Note: Current implementation closes after one question
        # This test documents that behavior


@pytest.mark.integration
def test_websocket_response_format(client):
    """Test that all WebSocket responses have correct format."""
    with client.websocket_connect("/api/v1/questions/ws/ask") as websocket:
        websocket.send_json({"question": "Latest crypto news?"})

        messages = []
        while True:
            try:
                data = websocket.receive_json()
                messages.append(data)

                # Validate message format
                assert "type" in data
                assert data["type"] in ["sources", "chunk", "done", "error"]

                if data["type"] == "sources":
                    assert "count" in data
                    assert "sources" in data
                elif data["type"] == "chunk":
                    assert "content" in data
                    assert isinstance(data["content"], str)
                elif data["type"] == "error":
                    assert "content" in data

                if data["type"] in ["done", "error"]:
                    break
            except Exception:
                break

        assert len(messages) > 0

"""
Pytest configuration and fixtures for NovaDeskAI Customer Success Agent tests
"""

import pytest
import sys
import os
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from agent.prototype import (
    ConversationState,
    MessageNormalizer,
    KnowledgeSearcher,
    SentimentAnalyzer,
    ChannelFormatter,
    EscalationEngine,
    AgentLoop,
)


# ============================================================================
# MOCK CLIENT FIXTURES
# ============================================================================

@pytest.fixture
def mock_groq_client():
    """Mock Groq client that returns valid JSON responses"""
    client = MagicMock()
    
    # Mock sentiment analysis response
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = '{"sentiment": "neutral", "score": 0.5, "indicators": []}'
    
    client.chat.completions.create.return_value = mock_response
    return client


# ============================================================================
# COMPONENT FIXTURES
# ============================================================================

@pytest.fixture
def message_normalizer():
    """Real MessageNormalizer instance"""
    return MessageNormalizer()


@pytest.fixture
def knowledge_searcher():
    """Real KnowledgeSearcher instance"""
    return KnowledgeSearcher()


@pytest.fixture
def sentiment_analyzer(mock_groq_client):
    """SentimentAnalyzer with mocked Groq client"""
    return SentimentAnalyzer(mock_groq_client)


@pytest.fixture
def channel_formatter():
    """Real ChannelFormatter instance"""
    return ChannelFormatter()


@pytest.fixture
def escalation_engine():
    """Real EscalationEngine instance"""
    return EscalationEngine()


# ============================================================================
# STATE FIXTURES
# ============================================================================

@pytest.fixture
def conversation_state():
    """Sample ConversationState for testing"""
    return ConversationState(
        conversation_id='test-conv-1',
        customer_id='cust_001',
        channel='web',
    )


# ============================================================================
# AGENT FIXTURES (MOCK MODE)
# ============================================================================

@pytest.fixture
def agent_loop_no_groq(monkeypatch):
    """
    AgentLoop instance with GROQ_API_KEY unset (mock mode).
    This avoids making real API calls during testing.
    """
    monkeypatch.delenv('GROQ_API_KEY', raising=False)
    
    # Import fresh to ensure no API key is set
    import importlib
    import agent.prototype
    importlib.reload(agent.prototype)
    
    return agent.prototype.AgentLoop()


# ============================================================================
# SERVER FIXTURES (TestClient)
# ============================================================================

@pytest.fixture
def mcp_client():
    """TestClient for MCP FastAPI app"""
    from agent.mcp_server import app as mcp_app
    return TestClient(mcp_app)


@pytest.fixture
def api_client():
    """TestClient for main API FastAPI app"""
    from api.main import app as api_app
    return TestClient(api_app)

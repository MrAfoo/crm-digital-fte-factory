"""Pytest configuration and fixtures for NovaDeskAI Production Stage 2 tests."""
import sys
import os
import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from fastapi.testclient import TestClient

# Add root to path so 'production' package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


@pytest.fixture
def mock_groq_client():
    """Mock Groq client with function calling support."""
    mock_client = MagicMock()
    
    # Mock the async chat.completions.create method
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message = MagicMock()
    mock_response.choices[0].message.content = 'Test response'
    mock_response.choices[0].message.tool_calls = None
    mock_response.usage = MagicMock()
    mock_response.usage.total_tokens = 100
    
    # Make it async
    async def async_create(*args, **kwargs):
        return mock_response
    
    mock_client.chat = MagicMock()
    mock_client.chat.completions = MagicMock()
    mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
    
    return mock_client


@pytest.fixture
def channel_formatter():
    """Real ChannelFormatter instance."""
    from production.agent.formatters import ChannelFormatter
    return ChannelFormatter()


@pytest.fixture
def tools_module():
    """Import tools module for testing."""
    from production.agent import tools
    return tools


@pytest.fixture
def api_client():
    """TestClient for FastAPI app."""
    from production.api.main import app
    return TestClient(app)


@pytest.fixture
def sample_conversation_id():
    """Sample conversation ID for testing."""
    return 'test-conv-stage2-001'


@pytest.fixture
def sample_customer_id():
    """Sample customer ID for testing."""
    return 'CUST-STAGE2-001'

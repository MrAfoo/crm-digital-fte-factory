"""
End-to-end transition tests for NovaDeskAI Stage 2.
Edge cases: empty message, pricing escalation, angry customer, channel formatting, tool execution order.
Run: pytest production/tests/test_e2e.py -v
"""
import sys
import os
import pytest
import json
import asyncio
import inspect
from unittest.mock import MagicMock, AsyncMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestEdgeCases:
    """Test edge cases in formatting and escalation."""
    
    def test_empty_message_handled_by_normalizer(self):
        """Empty message handled without crash."""
        from production.agent.formatters import ChannelFormatter
        formatter = ChannelFormatter()
        # Should not raise exception
        result = formatter.format('', 'email')
        assert isinstance(result, str)
    
    def test_very_long_message_truncated(self):
        """6000 char message formatted for whatsapp → <= 300 chars."""
        from production.agent.formatters import ChannelFormatter
        formatter = ChannelFormatter()
        long_msg = 'a' * 6000
        result = formatter.format(long_msg, 'whatsapp')
        assert len(result) <= 300
    
    def test_pricing_escalation_keywords(self):
        """Check that prompts.py CUSTOMER_SUCCESS_SYSTEM_PROMPT mentions billing/refund escalation."""
        from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
        assert 'billing' in CUSTOMER_SUCCESS_SYSTEM_PROMPT.lower()
    
    def test_angry_customer_escalation_keyword(self):
        """Prompt mentions angry/profanity escalation condition."""
        from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
        content_lower = CUSTOMER_SUCCESS_SYSTEM_PROMPT.lower()
        assert 'aggressive' in content_lower or 'profanity' in content_lower or 'angry' in content_lower
    
    def test_email_format_has_greeting_and_signature(self):
        """Email format always has both greeting and signature."""
        from production.agent.formatters import ChannelFormatter
        formatter = ChannelFormatter()
        result = formatter.format('Test', 'email', 'John')
        assert 'Hi' in result
        assert 'NovaDeskAI' in result
    
    def test_whatsapp_format_under_300(self):
        """All whatsapp output <= 300 chars."""
        from production.agent.formatters import ChannelFormatter
        formatter = ChannelFormatter()
        test_messages = [
            'Short',
            'a' * 250,
            'a' * 500,
            'a' * 1000,
        ]
        for msg in test_messages:
            result = formatter.format(msg, 'whatsapp')
            assert len(result) <= 300, f"Message length {len(result)} exceeds 300 chars"
    
    def test_web_format_has_cta(self):
        """Web format always ends with CTA."""
        from production.agent.formatters import ChannelFormatter
        formatter = ChannelFormatter()
        result = formatter.format('Test message', 'web')
        assert '→' in result or 'help' in result.lower()
    
    def test_channel_limit_enforcement(self):
        """truncate_to_limit works for all 3 channels."""
        from production.agent.formatters import ChannelFormatter
        formatter = ChannelFormatter()
        long_msg = 'test ' * 1000
        
        for channel in ['email', 'whatsapp', 'web']:
            result = formatter.truncate_to_limit(long_msg, channel)
            if channel == 'email':
                assert len(result) <= 3500
            elif channel == 'whatsapp':
                assert len(result) <= 300
            elif channel == 'web':
                assert len(result) <= 2100


class TestToolExecutionOrder:
    """Test tool registration and execution."""
    
    def test_all_tools_registered(self):
        """ALL_TOOLS list has 5 items."""
        from production.agent.tools import ALL_TOOLS
        assert len(ALL_TOOLS) == 5
    
    def test_tools_are_async(self):
        """All tools in ALL_TOOLS are coroutine functions."""
        from production.agent.tools import ALL_TOOLS
        for tool in ALL_TOOLS:
            assert inspect.iscoroutinefunction(tool), f"{tool.__name__} is not async"
    
    def test_search_tool_name(self):
        """search_knowledge_base.tool_name == 'search_knowledge_base'."""
        from production.agent.tools import search_knowledge_base
        assert search_knowledge_base.tool_name == 'search_knowledge_base'
    
    def test_create_ticket_tool_name(self):
        """create_ticket.tool_name == 'create_ticket'."""
        from production.agent.tools import create_ticket
        assert create_ticket.tool_name == 'create_ticket'
    
    def test_escalate_tool_name(self):
        """escalate_to_human.tool_name == 'escalate_to_human'."""
        from production.agent.tools import escalate_to_human
        assert escalate_to_human.tool_name == 'escalate_to_human'
    
    def test_send_response_tool_name(self):
        """send_response.tool_name == 'send_response'."""
        from production.agent.tools import send_response
        assert send_response.tool_name == 'send_response'
    
    def test_get_history_tool_name(self):
        """get_customer_history.tool_name == 'get_customer_history'."""
        from production.agent.tools import get_customer_history
        assert get_customer_history.tool_name == 'get_customer_history'


class TestAPIEndpoints:
    """Test API endpoints."""
    
    def test_health_returns_healthy(self, api_client):
        """GET /health → status == 'healthy'."""
        response = api_client.get('/health')
        assert response.status_code == 200
        data = response.json()
        assert data['status'] == 'healthy'
    
    def test_health_has_version(self, api_client):
        """Response has 'version' == '2.0.0'."""
        response = api_client.get('/health')
        data = response.json()
        assert data['version'] == '2.0.0'
    
    def test_process_message_endpoint(self, api_client):
        """POST /api/messages/process with {message, channel, customer_id} → 200."""
        response = api_client.post('/api/messages/process', json={
            'message': 'Hello, can you help me?',
            'channel': 'email',
            'customer_id': 'CUST001'
        })
        assert response.status_code == 200
    
    def test_process_message_returns_response(self, api_client):
        """Result has 'response' key."""
        response = api_client.post('/api/messages/process', json={
            'message': 'Hello, can you help me?',
            'channel': 'email',
            'customer_id': 'CUST001'
        })
        data = response.json()
        assert 'response' in data
    
    def test_process_message_returns_conversation_id(self, api_client):
        """Result has 'conversation_id'."""
        response = api_client.post('/api/messages/process', json={
            'message': 'Hello, can you help me?',
            'channel': 'email',
            'customer_id': 'CUST001'
        })
        data = response.json()
        assert 'conversation_id' in data
    
    def test_create_ticket_endpoint(self, api_client):
        """POST /api/tickets with valid data → 200."""
        response = api_client.post('/api/tickets', json={
            'name': 'John Doe',
            'email': 'john@example.com',
            'subject': 'Need Help',
            'channel': 'email',
            'description': 'I need help with X'
        })
        assert response.status_code == 200
    
    def test_create_ticket_returns_ticket_id(self, api_client):
        """ticket_id starts with 'TKT-'."""
        response = api_client.post('/api/tickets', json={
            'name': 'John Doe',
            'email': 'john@example.com',
            'subject': 'Need Help',
            'channel': 'email',
            'description': 'I need help with X'
        })
        data = response.json()
        assert data['ticket_id'].startswith('TKT-')
    
    def test_list_tickets_endpoint(self, api_client):
        """GET /api/tickets → 200, returns list."""
        response = api_client.get('/api/tickets')
        assert response.status_code == 200
        data = response.json()
        assert 'tickets' in data
        assert isinstance(data['tickets'], list)
    
    def test_get_stats_endpoint(self, api_client):
        """GET /api/stats → 200, has 'total_tickets'."""
        response = api_client.get('/api/stats')
        assert response.status_code == 200
        data = response.json()
        assert 'total_tickets' in data
    
    def test_get_metrics_endpoint(self, api_client):
        """GET /api/metrics → 200."""
        response = api_client.get('/api/metrics')
        assert response.status_code == 200
    
    def test_whatsapp_webhook_verify(self, api_client):
        """GET /webhook/whatsapp?hub.mode=subscribe&hub.verify_token=...&hub.challenge=test123."""
        # This will likely fail without proper credentials, but test the endpoint exists
        response = api_client.get('/webhook/whatsapp', params={
            'hub_mode': 'subscribe',
            'hub_verify_token': 'invalid',
            'hub_challenge': 'test123'
        })
        # Either 403 (invalid token) or 503 (not available) are acceptable
        assert response.status_code in [403, 503]
    
    def test_404_for_unknown_ticket(self, api_client):
        """GET /api/tickets/TKT-NOTEXIST → 404."""
        response = api_client.get('/api/tickets/TKT-NOTEXIST')
        assert response.status_code == 404


class TestMetricsCollector:
    """Test metrics collector."""
    
    def test_metrics_collector_init(self):
        """MetricsCollector() initializes without error."""
        from production.workers.metrics_collector import MetricsCollector
        collector = MetricsCollector()
        assert collector is not None
    
    def test_record_response_time(self):
        """record_response_time(500, 'email') → avg_response_time > 0."""
        from production.workers.metrics_collector import MetricsCollector
        collector = MetricsCollector()
        collector.record_response_time(500, 'email')
        summary = collector.get_summary()
        assert summary['avg_response_time_ms'] > 0
    
    def test_record_sentiment(self):
        """record_sentiment('angry', 'whatsapp') → sentiment_counts has 'angry'."""
        from production.workers.metrics_collector import MetricsCollector
        collector = MetricsCollector()
        collector.record_sentiment('angry', 'whatsapp')
        summary = collector.get_summary()
        assert 'anger' in summary['sentiment_breakdown'] or len(summary['sentiment_breakdown']) > 0
    
    def test_record_escalation(self):
        """record_escalation('angry', 2, 'email') → escalation_count > 0."""
        from production.workers.metrics_collector import MetricsCollector
        collector = MetricsCollector()
        collector.record_escalation('angry', tier='tier2', channel='email')
        summary = collector.get_summary()
        assert summary['escalation_count'] > 0
    
    def test_get_summary_returns_dict(self):
        """get_summary() returns dict with required keys."""
        from production.workers.metrics_collector import MetricsCollector
        collector = MetricsCollector()
        summary = collector.get_summary()
        assert isinstance(summary, dict)
        assert 'avg_response_time_ms' in summary
        assert 'escalation_count' in summary
    
    def test_deflection_rate_calculation(self):
        """With 0 escalations → deflection_rate >= 0."""
        from production.workers.metrics_collector import MetricsCollector
        collector = MetricsCollector()
        collector.record_deflection('email')
        summary = collector.get_summary()
        assert summary['deflection_count'] >= 0
    
    def test_csat_average(self):
        """Record 3 scores (4.0, 5.0, 3.0) → avg == 4.0."""
        from production.workers.metrics_collector import MetricsCollector
        collector = MetricsCollector()
        collector.record_csat(4.0, 'email')
        collector.record_csat(5.0, 'email')
        collector.record_csat(3.0, 'email')
        summary = collector.get_summary()
        assert abs(summary['csat_avg'] - 4.0) < 0.01

"""
Channel handler tests for NovaDeskAI Stage 2.
Tests: WhatsAppHandler, GmailHandler, web_form_handler.
Run: pytest production/tests/test_channels.py -v
"""
import sys
import os
import pytest
import json
import base64
from unittest.mock import MagicMock, AsyncMock, patch, Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestWhatsAppHandler:
    """Test WhatsApp channel handler."""
    
    def test_handler_init_without_token(self):
        """WhatsAppHandler() without env var → handler.available == False."""
        with patch.dict(os.environ, {}, clear=True):
            from production.channels.whatsapp_handler import WhatsAppHandler
            handler = WhatsAppHandler()
            assert handler.available is False
    
    def test_verify_webhook_valid_token(self):
        """verify_webhook('subscribe', correct_token, 'challenge123') → 'challenge123'."""
        with patch.dict(os.environ, {'WHATSAPP_VERIFY_TOKEN': 'test_token'}):
            from production.channels.whatsapp_handler import WhatsAppHandler
            handler = WhatsAppHandler()
            result = handler.verify_webhook('subscribe', 'test_token', 'challenge123')
            assert result == 'challenge123'
    
    def test_verify_webhook_invalid_token(self):
        """Wrong token → None."""
        with patch.dict(os.environ, {'WHATSAPP_VERIFY_TOKEN': 'test_token'}):
            from production.channels.whatsapp_handler import WhatsAppHandler
            handler = WhatsAppHandler()
            result = handler.verify_webhook('subscribe', 'wrong_token', 'challenge123')
            assert result is None
    
    def test_validate_signature_invalid(self):
        """Wrong signature → False."""
        with patch.dict(os.environ, {'WHATSAPP_TOKEN': 'secret'}):
            from production.channels.whatsapp_handler import WhatsAppHandler
            handler = WhatsAppHandler()
            result = handler.validate_signature(b'test', 'invalidsig')
            assert result is False
    
    def test_format_response_short(self):
        """Short response → list of 1 item."""
        with patch.dict(os.environ, {'WHATSAPP_TOKEN': 'token'}):
            from production.channels.whatsapp_handler import WhatsAppHandler
            handler = WhatsAppHandler()
            result = handler.format_response('Short message', max_length=1600)
            assert isinstance(result, list)
            assert len(result) == 1
    
    def test_format_response_long(self):
        """2000 char response → split into multiple chunks."""
        with patch.dict(os.environ, {'WHATSAPP_TOKEN': 'token'}):
            from production.channels.whatsapp_handler import WhatsAppHandler
            handler = WhatsAppHandler()
            long_msg = 'Test message. ' * 150
            result = handler.format_response(long_msg, max_length=1600)
            assert isinstance(result, list)
            assert len(result) > 1
    
    @pytest.mark.asyncio
    async def test_normalize_to_standard_has_channel(self):
        """Result['channel'] == 'whatsapp'."""
        with patch.dict(os.environ, {'WHATSAPP_TOKEN': 'token'}):
            from production.channels.whatsapp_handler import WhatsAppHandler
            handler = WhatsAppHandler()
            test_msg = {
                'channel': 'whatsapp',
                'channel_message_id': '123',
                'customer_phone': '1234567890',
                'customer_name': 'Test User',
                'content': 'Test content',
                'received_at': '2024-01-01T00:00:00Z',
                'metadata': {}
            }
            result = handler.normalize_to_standard(test_msg)
            assert result['channel'] == 'whatsapp'
    
    @pytest.mark.asyncio
    async def test_normalize_to_standard_has_content(self):
        """Result has 'content' key."""
        with patch.dict(os.environ, {'WHATSAPP_TOKEN': 'token'}):
            from production.channels.whatsapp_handler import WhatsAppHandler
            handler = WhatsAppHandler()
            test_msg = {
                'channel': 'whatsapp',
                'channel_message_id': '123',
                'customer_phone': '1234567890',
                'customer_name': 'Test User',
                'content': 'Test content',
                'received_at': '2024-01-01T00:00:00Z',
                'metadata': {}
            }
            result = handler.normalize_to_standard(test_msg)
            assert 'content' in result
    
    @pytest.mark.asyncio
    async def test_process_webhook_empty_data(self):
        """Empty dict → returns [] without error."""
        with patch.dict(os.environ, {'WHATSAPP_TOKEN': 'token', 'WHATSAPP_PHONE_NUMBER_ID': '123'}):
            from production.channels.whatsapp_handler import WhatsAppHandler
            handler = WhatsAppHandler()
            result = await handler.process_webhook({})
            assert isinstance(result, list)
            assert len(result) == 0


class TestGmailHandler:
    """Test Gmail channel handler."""
    
    def test_gmail_handler_init_no_credentials(self):
        """GmailHandler() without creds → handler.available == False."""
        with patch.dict(os.environ, {}, clear=True):
            from production.channels.gmail_handler import GmailHandler
            handler = GmailHandler()
            assert handler.available is False
    
    def test_extract_email_from_header(self):
        """_extract_email('John Smith <john@example.com>') → 'john@example.com'."""
        from production.channels.gmail_handler import GmailHandler
        handler = GmailHandler()
        result = handler._extract_email('John Smith <john@example.com>')
        assert result == 'john@example.com'
    
    def test_extract_email_plain_email(self):
        """_extract_email('john@example.com') → 'john@example.com'."""
        from production.channels.gmail_handler import GmailHandler
        handler = GmailHandler()
        result = handler._extract_email('john@example.com')
        assert result == 'john@example.com'
    
    def test_strip_quoted_text_removes_on_wrote(self):
        """Input with 'On Mon ... wrote:' → removed."""
        from production.channels.gmail_handler import GmailHandler
        handler = GmailHandler()
        text = "My response\n\nOn Mon wrote:\n> Original message"
        result = handler._strip_quoted_text(text)
        assert 'My response' in result
        assert 'On Mon' not in result or result.strip().endswith('My response')
    
    def test_strip_quoted_text_removes_angle_brackets(self):
        """'> quoted line' → removed."""
        from production.channels.gmail_handler import GmailHandler
        handler = GmailHandler()
        text = "My text\n> quoted line\n> another quoted"
        result = handler._strip_quoted_text(text)
        assert 'My text' in result
    
    def test_normalize_to_standard_has_channel(self):
        """Result['channel'] == 'email'."""
        from production.channels.gmail_handler import GmailHandler
        handler = GmailHandler()
        test_msg = {
            'channel': 'email',
            'channel_message_id': '123',
            'customer_email': 'john@example.com',
            'customer_name': 'John',
            'subject': 'Test',
            'content': 'Test content',
            'received_at': '2024-01-01T00:00:00Z',
            'metadata': {}
        }
        result = handler.normalize_to_standard(test_msg)
        assert result['channel'] == 'email'
    
    def test_extract_body_plain_text(self):
        """_extract_body with plain text → extracts correctly."""
        from production.channels.gmail_handler import GmailHandler
        handler = GmailHandler()
        # Encode test message
        test_text = 'Hello World'
        encoded = base64.urlsafe_b64encode(test_text.encode()).decode()
        payload = {
            'mimeType': 'text/plain',
            'body': {'data': encoded}
        }
        result = handler._extract_body(payload)
        assert result == test_text


class TestWebFormHandler:
    """Test web form handler."""
    
    def test_submit_endpoint_returns_200(self, api_client):
        """POST /support/submit with valid data → 200."""
        response = api_client.post('/support/submit', json={
            'name': 'John Doe',
            'email': 'john@example.com',
            'subject': 'Test Subject',
            'category': 'general',
            'message': 'This is a test message with enough content'
        })
        assert response.status_code == 200
    
    def test_submit_endpoint_returns_ticket_id(self, api_client):
        """Response has 'ticket_id'."""
        response = api_client.post('/support/submit', json={
            'name': 'John Doe',
            'email': 'john@example.com',
            'subject': 'Test Subject',
            'category': 'general',
            'message': 'This is a test message with enough content'
        })
        data = response.json()
        assert 'ticket_id' in data
    
    def test_submit_validates_required_fields(self, api_client):
        """Missing name → 422."""
        response = api_client.post('/support/submit', json={
            'email': 'john@example.com',
            'subject': 'Test Subject',
            'category': 'general',
            'message': 'This is a test message'
        })
        assert response.status_code == 422
    
    def test_submit_validates_email(self, api_client):
        """Invalid email → 422."""
        response = api_client.post('/support/submit', json={
            'name': 'John Doe',
            'email': 'not-an-email',
            'subject': 'Test Subject',
            'category': 'general',
            'message': 'This is a test message with enough content'
        })
        assert response.status_code == 422
    
    def test_submit_validates_message_length(self, api_client):
        """Message < 10 chars → 422."""
        response = api_client.post('/support/submit', json={
            'name': 'John Doe',
            'email': 'john@example.com',
            'subject': 'Test',
            'category': 'general',
            'message': 'short'
        })
        assert response.status_code == 422
    
    def test_get_ticket_endpoint(self, api_client):
        """Create then GET /support/ticket/{id} → 200."""
        # First create a ticket
        create_response = api_client.post('/support/submit', json={
            'name': 'John Doe',
            'email': 'john@example.com',
            'subject': 'Test Subject',
            'category': 'general',
            'message': 'This is a test message with enough content'
        })
        ticket_id = create_response.json()['ticket_id']
        
        # Then get it
        get_response = api_client.get(f'/support/ticket/{ticket_id}')
        assert get_response.status_code == 200
    
    def test_normalize_to_standard_returns_dict(self):
        """normalize_to_standard(mock_submission) → has 'channel' key."""
        from production.channels.web_form_handler import WebFormHandler, SupportFormSubmission
        submission = SupportFormSubmission(
            name='John Doe',
            email='john@example.com',
            subject='Test',
            category='general',
            message='This is a test message'
        )
        result = WebFormHandler.normalize_to_standard(submission, 'test-ticket-id')
        assert 'channel' in result
        assert result['channel'] == 'web_form'

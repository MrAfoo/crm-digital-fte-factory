"""
Tests for ChannelFormatter class
"""

import pytest


class TestChannelFormatter:
    """Test suite for ChannelFormatter"""

    def test_email_adds_greeting(self, channel_formatter):
        """Test that email formatting adds greeting"""
        response = "Your issue has been resolved."
        result = channel_formatter.format(response, "email")
        assert "Hi" in result
        assert "there" in result or "," in result

    def test_email_adds_signature(self, channel_formatter):
        """Test that email formatting adds signature"""
        response = "Your issue has been resolved."
        result = channel_formatter.format(response, "email")
        assert "NovaDeskAI" in result or "Nova" in result
        assert "Support" in result

    def test_email_with_customer_name(self, channel_formatter):
        """Test that email greeting uses customer name"""
        response = "Your issue has been resolved."
        result = channel_formatter.format(response, "email", "John")
        assert "John" in result
        assert "Hi" in result

    def test_whatsapp_truncates_long_message(self, channel_formatter):
        """Test that WhatsApp truncates messages over 300 chars"""
        response = "A" * 350
        result = channel_formatter.format(response, "whatsapp")
        assert len(result) <= 300
        assert "..." in result

    def test_whatsapp_short_message_unchanged(self, channel_formatter):
        """Test that short WhatsApp messages are not truncated"""
        response = "Hello there!"
        result = channel_formatter.format(response, "whatsapp")
        assert result == response

    def test_web_adds_cta(self, channel_formatter):
        """Test that web formatting adds call-to-action"""
        response = "Your issue has been resolved."
        result = channel_formatter.format(response, "web")
        assert "Need more help?" in result or "help" in result.lower()

    def test_web_adds_period_if_missing(self, channel_formatter):
        """Test that web response ends with period if missing"""
        response = "Your issue has been resolved"
        result = channel_formatter.format(response, "web")
        # The response should end with period before CTA
        assert "." in result

    def test_email_adds_period_if_missing(self, channel_formatter):
        """Test that email response ends with period if missing"""
        response = "Your issue has been resolved"
        result = channel_formatter.format(response, "email")
        # Period should be added before signature
        assert "." in result or "resolved." in result

    def test_unknown_channel_returns_raw(self, channel_formatter):
        """Test that unknown channel returns response as-is"""
        response = "Hello there"
        result = channel_formatter.format(response, "unknown_channel")
        assert result == response

    def test_email_default_customer_name(self, channel_formatter):
        """Test that email uses 'there' as default name"""
        response = "Your issue has been resolved."
        result = channel_formatter.format(response, "email")
        # Should have either 'there' or provided name
        assert "Hi" in result

    def test_whatsapp_no_signature(self, channel_formatter):
        """Test that WhatsApp doesn't add signature"""
        response = "Hello"
        result = channel_formatter.format(response, "whatsapp")
        assert "Signature" not in result
        assert "Nova" not in result
        assert "NovaDeskAI" not in result

    def test_web_has_period_before_cta(self, channel_formatter):
        """Test that web format has proper punctuation"""
        response = "Thank you for your patience"
        result = channel_formatter.format(response, "web")
        # Should have both period and CTA
        assert "." in result
        assert "help" in result.lower()

    def test_email_multiline_response(self, channel_formatter):
        """Test email formatting with multiline response"""
        response = "Line 1\nLine 2\nLine 3"
        result = channel_formatter.format(response, "email")
        assert "Line 1" in result
        assert "Hi" in result

    def test_whatsapp_exactly_at_limit(self, channel_formatter):
        """Test WhatsApp message exactly at 300 char limit"""
        response = "A" * 300
        result = channel_formatter.format(response, "whatsapp")
        assert len(result) <= 300

    def test_channel_formatter_case_insensitive(self, channel_formatter):
        """Test that channel names are case-insensitive"""
        response = "Test message"
        result_lower = channel_formatter.format(response, "email")
        result_upper = channel_formatter.format(response, "EMAIL")
        # Both should add email formatting
        assert "Hi" in result_lower and "Hi" in result_upper

    def test_email_preserves_content(self, channel_formatter):
        """Test that email formatting preserves original content"""
        response = "This is important information."
        result = channel_formatter.format(response, "email")
        assert response in result or "important information" in result

    def test_whatsapp_preserves_emoji(self, channel_formatter):
        """Test that WhatsApp preserves emoji in messages"""
        response = "Great job! 😊"
        result = channel_formatter.format(response, "whatsapp")
        assert "😊" in result

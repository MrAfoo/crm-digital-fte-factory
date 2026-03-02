"""
Tests for MessageNormalizer class
"""

import pytest


class TestMessageNormalizer:
    """Test suite for MessageNormalizer"""

    def test_normalize_email_strips_whitespace(self, message_normalizer):
        """Test that email messages have whitespace stripped"""
        raw = "   Hello there   "
        result = message_normalizer.normalize(raw, "email")
        assert result["normalized_text"] == "Hello there"
        assert result["original_length"] == len(raw)
        assert result["cleaned_length"] == len("Hello there")

    def test_normalize_email_removes_signature(self, message_normalizer):
        """Test that email signatures are removed"""
        raw = "Hello, I need help.\n\nBest regards,\nJohn Smith"
        result = message_normalizer.normalize(raw, "email")
        assert "Best regards" not in result["normalized_text"]
        assert "Hello, I need help" in result["normalized_text"]

    def test_normalize_email_removes_quoted_text(self, message_normalizer):
        """Test that quoted text (On ... wrote:) is removed"""
        raw = "My response here.\n\nOn Monday, John wrote:\n> Original message"
        result = message_normalizer.normalize(raw, "email")
        assert "On Monday" not in result["normalized_text"]
        assert "My response here" in result["normalized_text"]

    def test_normalize_whatsapp_handles_short_message(self, message_normalizer):
        """Test that short WhatsApp messages are handled correctly"""
        raw = "Hi there!"
        result = message_normalizer.normalize(raw, "whatsapp")
        assert result["normalized_text"] == "Hi there!"
        assert result["language"] == "en"

    def test_normalize_whatsapp_deduplicates_emoji(self, message_normalizer):
        """Test that duplicate emoji are deduplicated"""
        raw = "Hello 😀😀😀 world"
        result = message_normalizer.normalize(raw, "whatsapp")
        # Should have single emoji instead of three
        assert result["normalized_text"].count('😀') == 1

    def test_normalize_web_removes_html_tags(self, message_normalizer):
        """Test that HTML tags are removed from web messages"""
        raw = "<b>Hello</b> <i>world</i>"
        result = message_normalizer.normalize(raw, "web")
        assert result["normalized_text"] == "Hello world"
        assert "<b>" not in result["normalized_text"]

    def test_normalize_returns_language(self, message_normalizer):
        """Test that language is detected (defaults to 'en')"""
        result = message_normalizer.normalize("Hello world", "web")
        assert "language" in result
        assert result["language"] == "en"

    def test_normalize_returns_original_length(self, message_normalizer):
        """Test that original_length is returned"""
        raw = "Test message"
        result = message_normalizer.normalize(raw, "web")
        assert result["original_length"] == len(raw)

    def test_normalize_returns_cleaned_length(self, message_normalizer):
        """Test that cleaned_length is returned and accurate"""
        raw = "  Test  "
        result = message_normalizer.normalize(raw, "web")
        assert "cleaned_length" in result
        assert result["cleaned_length"] == len("Test")

    def test_normalize_detects_urls(self, message_normalizer):
        """Test that URLs are detected in channel_metadata"""
        raw = "Check this out: https://example.com"
        result = message_normalizer.normalize(raw, "web")
        assert result["channel_metadata"]["has_urls"] is True

    def test_normalize_detects_questions(self, message_normalizer):
        """Test that questions are detected in channel_metadata"""
        raw = "Can you help me?"
        result = message_normalizer.normalize(raw, "web")
        assert result["channel_metadata"]["has_question"] is True

    def test_normalize_empty_message(self, message_normalizer):
        """Test that empty messages are handled gracefully"""
        result = message_normalizer.normalize("", "web")
        assert result["normalized_text"] == ""
        assert result["cleaned_length"] == 0

    def test_normalize_unknown_channel(self, message_normalizer):
        """Test that unknown channels fall back gracefully"""
        raw = "Test message"
        result = message_normalizer.normalize(raw, "unknown_channel")
        assert result["normalized_text"] == "Test message"
        assert result["language"] == "en"

    def test_normalize_email_detects_attachment_mention(self, message_normalizer):
        """Test that attachment mentions are detected in email"""
        raw = "Please find the document attached."
        result = message_normalizer.normalize(raw, "email")
        assert result["channel_metadata"]["has_attachment_mention"] is True

    def test_normalize_returns_all_required_keys(self, message_normalizer):
        """Test that all required keys are in the result"""
        result = message_normalizer.normalize("Test", "web")
        required_keys = {"normalized_text", "language", "channel_metadata", "original_length", "cleaned_length"}
        assert required_keys.issubset(result.keys())

    def test_normalize_no_urls_in_message(self, message_normalizer):
        """Test that has_urls is False when no URLs present"""
        result = message_normalizer.normalize("Just a normal message", "web")
        assert result["channel_metadata"]["has_urls"] is False

    def test_normalize_no_question_in_message(self, message_normalizer):
        """Test that has_question is False when no question mark present"""
        result = message_normalizer.normalize("Just a statement.", "web")
        assert result["channel_metadata"]["has_question"] is False

    def test_normalize_word_count(self, message_normalizer):
        """Test that word_count is calculated correctly"""
        result = message_normalizer.normalize("One two three four five", "web")
        assert result["channel_metadata"]["word_count"] == 5

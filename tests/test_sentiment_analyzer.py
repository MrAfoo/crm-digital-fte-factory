"""
Tests for SentimentAnalyzer class
"""

import json
import pytest
from unittest.mock import MagicMock


class TestSentimentAnalyzer:
    """Test suite for SentimentAnalyzer"""

    def test_analyze_returns_dict(self, sentiment_analyzer, mock_groq_client):
        """Test that analyze returns a dictionary"""
        result = sentiment_analyzer.analyze("Hello, I need help")
        assert isinstance(result, dict)

    def test_analyze_has_sentiment_key(self, sentiment_analyzer, mock_groq_client):
        """Test that result has 'sentiment' key"""
        result = sentiment_analyzer.analyze("Great job!")
        assert "sentiment" in result

    def test_analyze_has_score_key(self, sentiment_analyzer, mock_groq_client):
        """Test that result has 'score' key"""
        result = sentiment_analyzer.analyze("Great job!")
        assert "score" in result

    def test_analyze_has_indicators_key(self, sentiment_analyzer, mock_groq_client):
        """Test that result has 'indicators' key"""
        result = sentiment_analyzer.analyze("Great job!")
        assert "indicators" in result

    def test_analyze_sentiment_is_valid_type(self, sentiment_analyzer, mock_groq_client):
        """Test that sentiment is one of the valid types"""
        result = sentiment_analyzer.analyze("Test message")
        valid_sentiments = {"positive", "neutral", "frustrated", "angry"}
        assert result["sentiment"] in valid_sentiments

    def test_analyze_score_between_0_and_1(self, sentiment_analyzer, mock_groq_client):
        """Test that score is between 0 and 1"""
        result = sentiment_analyzer.analyze("Test message")
        assert 0 <= result["score"] <= 1

    def test_analyze_fallback_on_json_error(self, sentiment_analyzer, mock_groq_client):
        """Test fallback behavior when JSON parsing fails"""
        # Make mock return invalid JSON
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is not JSON"
        mock_groq_client.chat.completions.create.return_value = mock_response
        
        result = sentiment_analyzer.analyze("Test message")
        # Should return neutral fallback
        assert result["sentiment"] == "neutral"
        assert result["score"] == 0.5

    def test_analyze_with_history(self, sentiment_analyzer, mock_groq_client):
        """Test that analyze processes conversation history"""
        history = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"}
        ]
        result = sentiment_analyzer.analyze("I still need help", history=history)
        # Should not raise an error
        assert isinstance(result, dict)

    def test_analyze_angry_message(self, sentiment_analyzer, mock_groq_client):
        """Test analyzing an angry message"""
        # Configure mock to return angry sentiment
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"sentiment": "angry", "score": 0.95, "indicators": ["!!!"]}'
        mock_groq_client.chat.completions.create.return_value = mock_response
        
        result = sentiment_analyzer.analyze("THIS IS ABSOLUTELY UNACCEPTABLE!!!")
        assert result["sentiment"] == "angry"

    def test_analyze_positive_message(self, sentiment_analyzer, mock_groq_client):
        """Test analyzing a positive message"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"sentiment": "positive", "score": 0.85, "indicators": ["love", "great"]}'
        mock_groq_client.chat.completions.create.return_value = mock_response
        
        result = sentiment_analyzer.analyze("I absolutely love your service!")
        assert result["sentiment"] == "positive"

    def test_analyze_frustrated_message(self, sentiment_analyzer, mock_groq_client):
        """Test analyzing a frustrated message"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = '{"sentiment": "frustrated", "score": 0.7, "indicators": ["not working"]}'
        mock_groq_client.chat.completions.create.return_value = mock_response
        
        result = sentiment_analyzer.analyze("This still isn't working...")
        assert result["sentiment"] == "frustrated"

    def test_analyze_indicators_is_list(self, sentiment_analyzer, mock_groq_client):
        """Test that indicators is a list"""
        result = sentiment_analyzer.analyze("Test")
        assert isinstance(result["indicators"], list)

    def test_analyze_with_empty_history(self, sentiment_analyzer, mock_groq_client):
        """Test analyze with empty history list"""
        result = sentiment_analyzer.analyze("Test", history=[])
        assert isinstance(result, dict)

    def test_analyze_with_none_history(self, sentiment_analyzer, mock_groq_client):
        """Test analyze with None history"""
        result = sentiment_analyzer.analyze("Test", history=None)
        assert isinstance(result, dict)

    def test_analyze_score_format(self, sentiment_analyzer, mock_groq_client):
        """Test that score is numeric"""
        result = sentiment_analyzer.analyze("Test")
        assert isinstance(result["score"], (int, float))

    def test_analyze_calls_groq_client(self, sentiment_analyzer, mock_groq_client):
        """Test that analyze calls the Groq client"""
        sentiment_analyzer.analyze("Test message")
        mock_groq_client.chat.completions.create.assert_called()

    def test_analyze_neutral_by_default(self, sentiment_analyzer, mock_groq_client):
        """Test that default mock returns neutral sentiment"""
        result = sentiment_analyzer.analyze("Any message")
        # The default mock is set to return neutral
        assert result["sentiment"] == "neutral"

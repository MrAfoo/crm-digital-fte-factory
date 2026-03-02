"""
Tests for AgentLoop orchestrator
"""

import pytest


class TestAgentLoopProcessMessage:
    """Test suite for AgentLoop.process_message() method"""

    def test_process_message_returns_dict(self, agent_loop_no_groq):
        """Test that process_message returns a dictionary"""
        result = agent_loop_no_groq.process_message(
            "Hello, I need help",
            "web",
            "cust_001"
        )
        assert isinstance(result, dict)

    def test_process_message_has_conversation_id(self, agent_loop_no_groq):
        """Test that result includes conversation_id"""
        result = agent_loop_no_groq.process_message(
            "Hello",
            "web",
            "cust_001"
        )
        assert "conversation_id" in result
        assert result["conversation_id"] is not None

    def test_process_message_has_response(self, agent_loop_no_groq):
        """Test that result includes response"""
        result = agent_loop_no_groq.process_message(
            "Hello",
            "web",
            "cust_001"
        )
        assert "response" in result
        assert isinstance(result["response"], str)

    def test_process_message_has_formatted_response(self, agent_loop_no_groq):
        """Test that result includes formatted_response"""
        result = agent_loop_no_groq.process_message(
            "Hello",
            "web",
            "cust_001"
        )
        assert "formatted_response" in result
        assert isinstance(result["formatted_response"], str)

    def test_process_message_has_sentiment(self, agent_loop_no_groq):
        """Test that result includes sentiment"""
        result = agent_loop_no_groq.process_message(
            "Hello",
            "web",
            "cust_001"
        )
        assert "sentiment" in result

    def test_process_message_creates_conversation(self, agent_loop_no_groq):
        """Test that processing creates a conversation"""
        result = agent_loop_no_groq.process_message(
            "Hello",
            "web",
            "cust_001"
        )
        conv_id = result["conversation_id"]
        assert conv_id in agent_loop_no_groq.conversations

    def test_process_message_reuses_conversation(self, agent_loop_no_groq):
        """Test that same conversation_id is reused on second call"""
        # First message
        result1 = agent_loop_no_groq.process_message(
            "Hello",
            "web",
            "cust_001"
        )
        conv_id = result1["conversation_id"]
        
        # Second message with same conversation
        result2 = agent_loop_no_groq.process_message(
            "I still need help",
            "web",
            "cust_001",
            conversation_id=conv_id
        )
        assert result2["conversation_id"] == conv_id

    def test_process_message_email_channel(self, agent_loop_no_groq):
        """Test processing message on email channel"""
        result = agent_loop_no_groq.process_message(
            "I forgot my password",
            "email",
            "cust_001"
        )
        assert result["channel"] == "email"
        assert "Hi" in result["formatted_response"]  # Email has greeting

    def test_process_message_whatsapp_channel(self, agent_loop_no_groq):
        """Test processing message on WhatsApp channel"""
        result = agent_loop_no_groq.process_message(
            "Hey, I need help!",
            "whatsapp",
            "cust_001"
        )
        assert result["channel"] == "whatsapp"

    def test_process_message_web_channel(self, agent_loop_no_groq):
        """Test processing message on web channel"""
        result = agent_loop_no_groq.process_message(
            "Can you help?",
            "web",
            "cust_001"
        )
        assert result["channel"] == "web"

    def test_process_message_returns_topics(self, agent_loop_no_groq):
        """Test that result includes topics list"""
        result = agent_loop_no_groq.process_message(
            "Hello",
            "web",
            "cust_001"
        )
        assert "topics" in result
        assert isinstance(result["topics"], list)

    def test_process_message_returns_escalated(self, agent_loop_no_groq):
        """Test that result includes escalated boolean"""
        result = agent_loop_no_groq.process_message(
            "Hello",
            "web",
            "cust_001"
        )
        assert "escalated" in result
        assert isinstance(result["escalated"], bool)

    def test_process_message_returns_escalation_details(self, agent_loop_no_groq):
        """Test that result includes escalation_details"""
        result = agent_loop_no_groq.process_message(
            "Hello",
            "web",
            "cust_001"
        )
        assert "escalation_details" in result

    def test_conversation_state_updated_after_message(self, agent_loop_no_groq):
        """Test that conversation state's message list grows"""
        # First message
        result1 = agent_loop_no_groq.process_message(
            "Message 1",
            "web",
            "cust_001"
        )
        conv_id = result1["conversation_id"]
        conv1 = agent_loop_no_groq.get_conversation(conv_id)
        initial_count = len(conv1.messages)
        
        # Second message
        agent_loop_no_groq.process_message(
            "Message 2",
            "web",
            "cust_001",
            conversation_id=conv_id
        )
        conv2 = agent_loop_no_groq.get_conversation(conv_id)
        assert len(conv2.messages) > initial_count

    def test_resolution_status_changes_to_in_progress(self, agent_loop_no_groq):
        """Test that resolution_status changes to in_progress"""
        result = agent_loop_no_groq.process_message(
            "Hello",
            "web",
            "cust_001"
        )
        conv = agent_loop_no_groq.get_conversation(result["conversation_id"])
        assert conv.resolution_status == "in_progress"


class TestAgentLoopGetConversation:
    """Test suite for AgentLoop.get_conversation() method"""

    def test_get_conversation_returns_state(self, agent_loop_no_groq):
        """Test that get_conversation returns ConversationState"""
        result = agent_loop_no_groq.process_message(
            "Hello",
            "web",
            "cust_001"
        )
        conv_id = result["conversation_id"]
        conv = agent_loop_no_groq.get_conversation(conv_id)
        
        assert conv is not None
        assert conv.conversation_id == conv_id

    def test_get_conversation_none_for_unknown(self, agent_loop_no_groq):
        """Test that get_conversation returns None for unknown ID"""
        result = agent_loop_no_groq.get_conversation("nonexistent-id")
        assert result is None

    def test_get_conversation_preserves_state(self, agent_loop_no_groq):
        """Test that retrieved conversation preserves state"""
        result = agent_loop_no_groq.process_message(
            "Hello",
            "web",
            "cust_001"
        )
        conv_id = result["conversation_id"]
        
        conv = agent_loop_no_groq.get_conversation(conv_id)
        assert conv.customer_id == "cust_001"
        assert conv.channel == "web"

    def test_get_conversation_after_multiple_messages(self, agent_loop_no_groq):
        """Test retrieving conversation after multiple messages"""
        result1 = agent_loop_no_groq.process_message(
            "Message 1",
            "web",
            "cust_001"
        )
        conv_id = result1["conversation_id"]
        
        agent_loop_no_groq.process_message(
            "Message 2",
            "web",
            "cust_001",
            conversation_id=conv_id
        )
        
        conv = agent_loop_no_groq.get_conversation(conv_id)
        assert len(conv.messages) >= 4  # 2 user + 2 assistant messages


class TestAgentLoopIntegration:
    """Integration tests for AgentLoop"""

    def test_multi_turn_conversation(self, agent_loop_no_groq):
        """Test multi-turn conversation flow"""
        # Start conversation
        result1 = agent_loop_no_groq.process_message(
            "I forgot my password",
            "web",
            "cust_001"
        )
        conv_id = result1["conversation_id"]
        
        # Follow-up message
        result2 = agent_loop_no_groq.process_message(
            "I didn't receive the reset email",
            "web",
            "cust_001",
            conversation_id=conv_id
        )
        
        # Both should have same conversation_id
        assert result2["conversation_id"] == conv_id
        
        # Conversation should have history
        conv = agent_loop_no_groq.get_conversation(conv_id)
        assert len(conv.messages) >= 4

    def test_different_customers_different_conversations(self, agent_loop_no_groq):
        """Test that different customers get different conversations"""
        result1 = agent_loop_no_groq.process_message(
            "Hello",
            "web",
            "cust_001"
        )
        
        result2 = agent_loop_no_groq.process_message(
            "Hello",
            "web",
            "cust_002"
        )
        
        assert result1["conversation_id"] != result2["conversation_id"]

    def test_channel_specific_formatting(self, agent_loop_no_groq):
        """Test that formatting is channel-specific"""
        result_email = agent_loop_no_groq.process_message(
            "Help",
            "email",
            "cust_001"
        )
        
        result_whatsapp = agent_loop_no_groq.process_message(
            "Help",
            "whatsapp",
            "cust_002"
        )
        
        # Email should have greeting, WhatsApp should not
        assert "Hi" in result_email["formatted_response"]
        assert len(result_whatsapp["formatted_response"]) <= 300  # WhatsApp limit

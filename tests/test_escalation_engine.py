"""
Tests for EscalationEngine class
"""

import pytest


class TestEscalationEngineShouldEscalate:
    """Test suite for EscalationEngine.should_escalate() method"""

    def test_no_escalation_for_neutral(self, escalation_engine, conversation_state):
        """Test that neutral sentiment doesn't trigger escalation"""
        sentiment_result = {"sentiment": "neutral", "score": 0.5, "indicators": []}
        result = escalation_engine.should_escalate(conversation_state, sentiment_result)
        assert result["escalate"] is False
        assert result["tier"] == 1

    def test_no_escalation_for_positive(self, escalation_engine, conversation_state):
        """Test that positive sentiment doesn't trigger escalation"""
        sentiment_result = {"sentiment": "positive", "score": 0.9, "indicators": ["happy"]}
        result = escalation_engine.should_escalate(conversation_state, sentiment_result)
        assert result["escalate"] is False
        assert result["tier"] == 1

    def test_escalates_angry_to_tier2(self, escalation_engine, conversation_state):
        """Test that angry sentiment escalates to tier 2"""
        sentiment_result = {"sentiment": "angry", "score": 0.9, "indicators": ["!!!", "ALL_CAPS"]}
        result = escalation_engine.should_escalate(conversation_state, sentiment_result)
        assert result["escalate"] is True
        assert result["tier"] == 2

    def test_escalates_angry_p1_to_tier3(self, escalation_engine, conversation_state):
        """Test that angry + P1 priority escalates to tier 3"""
        conversation_state.metadata["priority"] = "P1"
        sentiment_result = {"sentiment": "angry", "score": 0.95, "indicators": ["critical"]}
        result = escalation_engine.should_escalate(conversation_state, sentiment_result)
        assert result["escalate"] is True
        assert result["tier"] == 3

    def test_escalates_frustrated_with_2_failures(self, escalation_engine, conversation_state):
        """Test that frustrated + 2 failed attempts escalates to tier 2"""
        conversation_state.failed_attempts = 2
        sentiment_result = {"sentiment": "frustrated", "score": 0.7, "indicators": ["not working"]}
        result = escalation_engine.should_escalate(conversation_state, sentiment_result)
        assert result["escalate"] is True
        assert result["tier"] == 2

    def test_escalates_3_failed_attempts(self, escalation_engine, conversation_state):
        """Test that 3+ failed attempts escalate to tier 2"""
        conversation_state.failed_attempts = 3
        sentiment_result = {"sentiment": "neutral", "score": 0.5, "indicators": []}
        result = escalation_engine.should_escalate(conversation_state, sentiment_result)
        assert result["escalate"] is True
        assert result["tier"] == 2

    def test_escalates_previously_escalated(self, escalation_engine, conversation_state):
        """Test that previously escalated conversations stay escalated"""
        conversation_state.resolution_status = "escalated"
        sentiment_result = {"sentiment": "neutral", "score": 0.5, "indicators": []}
        result = escalation_engine.should_escalate(conversation_state, sentiment_result)
        assert result["escalate"] is True
        assert result["tier"] == 2

    def test_escalation_returns_bool_tier_reason(self, escalation_engine, conversation_state):
        """Test that should_escalate returns proper dict structure"""
        sentiment_result = {"sentiment": "angry", "score": 0.9, "indicators": []}
        result = escalation_engine.should_escalate(conversation_state, sentiment_result)
        assert "escalate" in result
        assert "tier" in result
        assert "reason" in result
        assert isinstance(result["escalate"], bool)
        assert isinstance(result["tier"], int)
        assert isinstance(result["reason"], str)

    def test_frustrated_without_failures_no_escalation(self, escalation_engine, conversation_state):
        """Test that frustrated alone (no failures) doesn't escalate"""
        sentiment_result = {"sentiment": "frustrated", "score": 0.6, "indicators": []}
        result = escalation_engine.should_escalate(conversation_state, sentiment_result)
        assert result["escalate"] is False

    def test_two_failures_without_frustrated_no_escalation(self, escalation_engine, conversation_state):
        """Test that 2 failures without frustrated sentiment doesn't escalate"""
        conversation_state.failed_attempts = 2
        sentiment_result = {"sentiment": "neutral", "score": 0.5, "indicators": []}
        result = escalation_engine.should_escalate(conversation_state, sentiment_result)
        assert result["escalate"] is False


class TestEscalationEngineEscalate:
    """Test suite for EscalationEngine.escalate() method"""

    def test_escalate_tier1_assigns_bot(self, escalation_engine, conversation_state):
        """Test that tier 1 escalation assigns to bot"""
        result = escalation_engine.escalate(conversation_state, 1, "test reason")
        assert "assigned_to" in result
        assert result["assigned_to"] == "bot"

    def test_escalate_tier2_assigns_agent(self, escalation_engine, conversation_state):
        """Test that tier 2 escalation assigns to agent"""
        result = escalation_engine.escalate(conversation_state, 2, "customer frustrated")
        assert result["assigned_to"] == "agent@novadesk.ai"

    def test_escalate_tier3_assigns_senior(self, escalation_engine, conversation_state):
        """Test that tier 3 escalation assigns to senior"""
        result = escalation_engine.escalate(conversation_state, 3, "critical P1 issue")
        assert result["assigned_to"] == "senior@novadesk.ai"

    def test_escalate_updates_state_status(self, escalation_engine, conversation_state):
        """Test that escalate updates conversation state"""
        initial_status = conversation_state.resolution_status
        escalation_engine.escalate(conversation_state, 2, "test")
        assert conversation_state.resolution_status == "escalated"

    def test_escalate_returns_escalation_record(self, escalation_engine, conversation_state):
        """Test that escalate returns proper escalation record"""
        result = escalation_engine.escalate(conversation_state, 2, "reason")
        assert "escalation_id" in result
        assert "conversation_id" in result
        assert "customer_id" in result
        assert "tier" in result
        assert "reason" in result
        assert "assigned_to" in result
        assert "expected_response_time" in result
        assert "created_at" in result

    def test_escalate_record_has_expected_response_time(self, escalation_engine, conversation_state):
        """Test that escalation record has proper response time"""
        result = escalation_engine.escalate(conversation_state, 2, "reason")
        assert result["expected_response_time"] in ["2 hours", "30 minutes", "15 minutes"]

    def test_escalate_tier1_response_time(self, escalation_engine, conversation_state):
        """Test tier 1 has correct response time"""
        result = escalation_engine.escalate(conversation_state, 1, "reason")
        assert result["expected_response_time"] == "2 hours"

    def test_escalate_tier2_response_time(self, escalation_engine, conversation_state):
        """Test tier 2 has correct response time"""
        result = escalation_engine.escalate(conversation_state, 2, "reason")
        assert result["expected_response_time"] == "30 minutes"

    def test_escalate_tier3_response_time(self, escalation_engine, conversation_state):
        """Test tier 3 has correct response time"""
        result = escalation_engine.escalate(conversation_state, 3, "reason")
        assert result["expected_response_time"] == "15 minutes"

    def test_escalate_stores_tier_in_metadata(self, escalation_engine, conversation_state):
        """Test that escalation tier is stored in state metadata"""
        escalation_engine.escalate(conversation_state, 2, "reason")
        assert conversation_state.metadata.get("escalation_tier") == 2

    def test_escalate_updates_timestamp(self, escalation_engine, conversation_state):
        """Test that escalate updates the state timestamp"""
        initial_updated = conversation_state.updated_at
        escalation_engine.escalate(conversation_state, 2, "reason")
        assert conversation_state.updated_at != initial_updated or conversation_state.updated_at is not None

    def test_escalate_record_has_conversation_id(self, escalation_engine, conversation_state):
        """Test that escalation record contains conversation ID"""
        result = escalation_engine.escalate(conversation_state, 2, "reason")
        assert result["conversation_id"] == conversation_state.conversation_id

    def test_escalate_record_has_customer_id(self, escalation_engine, conversation_state):
        """Test that escalation record contains customer ID"""
        result = escalation_engine.escalate(conversation_state, 2, "reason")
        assert result["customer_id"] == conversation_state.customer_id

    def test_escalate_record_has_reason(self, escalation_engine, conversation_state):
        """Test that escalation record preserves reason"""
        reason = "Customer very angry about billing"
        result = escalation_engine.escalate(conversation_state, 2, reason)
        assert result["reason"] == reason

    def test_escalate_id_is_unique(self, escalation_engine, conversation_state):
        """Test that each escalation gets unique ID"""
        result1 = escalation_engine.escalate(conversation_state, 2, "reason 1")
        result2 = escalation_engine.escalate(conversation_state, 2, "reason 2")
        assert result1["escalation_id"] != result2["escalation_id"]

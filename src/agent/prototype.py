"""
Customer Success AI Agent - Core Prototype Loop
Uses Groq LLM (llama-3.3-70b-versatile) with FastAPI-ready architecture
"""

import os
import json
import uuid
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
import re
from collections import defaultdict

from groq import Groq
from dotenv import load_dotenv
load_dotenv()


# ============================================================================
# ENUMS & CONSTANTS
# ============================================================================

class SentimentType(str, Enum):
    POSITIVE = "positive"
    NEUTRAL = "neutral"
    FRUSTRATED = "frustrated"
    ANGRY = "angry"


class ResolutionStatus(str, Enum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    ESCALATED = "escalated"


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class ConversationState:
    """Tracks conversation context, sentiment, and resolution status"""
    conversation_id: str
    customer_id: str
    channel: str
    messages: List[Dict[str, Any]] = field(default_factory=list)
    sentiment: str = SentimentType.NEUTRAL
    topics: List[str] = field(default_factory=list)
    resolution_status: str = ResolutionStatus.OPEN
    failed_attempts: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return asdict(self)


# ============================================================================
# MESSAGE NORMALIZER
# ============================================================================

class MessageNormalizer:
    """Normalizes raw messages and extracts channel-specific metadata"""

    def normalize(self, raw_message: str, channel: str) -> Dict[str, Any]:
        """
        Normalize message based on channel
        
        Args:
            raw_message: Raw input message
            channel: 'email', 'whatsapp', or 'web'
            
        Returns:
            {
                'normalized_text': str,
                'language': str,
                'channel_metadata': dict,
                'original_length': int,
                'cleaned_length': int
            }
        """
        original_length = len(raw_message)
        
        # Basic whitespace cleanup
        normalized = raw_message.strip()
        
        # Channel-specific cleaning
        if channel.lower() == "email":
            normalized = self._clean_email(normalized)
        elif channel.lower() == "whatsapp":
            normalized = self._clean_whatsapp(normalized)
        elif channel.lower() == "web":
            normalized = self._clean_web(normalized)
        
        # Detect language (simple heuristic)
        language = self._detect_language(normalized)
        
        # Extract channel-specific metadata
        channel_metadata = self._extract_channel_metadata(normalized, channel)
        
        return {
            "normalized_text": normalized,
            "language": language,
            "channel_metadata": channel_metadata,
            "original_length": original_length,
            "cleaned_length": len(normalized),
        }

    def _clean_email(self, text: str) -> str:
        """Remove email signatures and quoted text"""
        # Patterns that match from a trigger word to end of string (re.DOTALL)
        tail_patterns = [
            r"--\s*\n.*",           # -- on its own line
            r"Best regards[\s\S]*",
            r"Sincerely[\s\S]*",
        ]
        # Patterns that match a single line (re.MULTILINE, not DOTALL)
        line_patterns = [
            r"^On .+wrote:\s*$",    # Quoted text marker line
            r"^From:.*$",           # Email header line
        ]
        # Patterns that strip quoted reply lines (lines starting with >)
        quoted_patterns = [
            r"^>.*$",               # Lines starting with >
        ]

        result = text
        for pattern in tail_patterns:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE)
        for pattern in line_patterns:
            result = re.sub(pattern, "", result, flags=re.IGNORECASE | re.MULTILINE)
        for pattern in quoted_patterns:
            result = re.sub(pattern, "", result, flags=re.MULTILINE)

        return result.strip()

    def _clean_whatsapp(self, text: str) -> str:
        """Handle WhatsApp-specific cleanup"""
        # Remove excessive emoji and normalize
        # Keep single instances of emoji
        text = re.sub(r'([😀-🙏])\1+', r'\1', text)
        return text.strip()

    def _clean_web(self, text: str) -> str:
        """Standard cleanup for web chat"""
        # Remove HTML tags if present
        text = re.sub(r'<[^>]+>', '', text)
        return text.strip()

    def _detect_language(self, text: str) -> str:
        """Simple language detection (returns 'en' for now, extensible)"""
        # TODO: Implement proper language detection with langdetect
        return "en"

    def _extract_channel_metadata(self, text: str, channel: str) -> Dict[str, Any]:
        """Extract channel-specific metadata"""
        metadata = {
            "has_urls": bool(re.search(r'http[s]?://', text)),
            "has_emoji": bool(re.search(r'[😀-🙏]', text)),
            "has_question": "?" in text,
            "word_count": len(text.split()),
        }
        
        if channel.lower() == "email":
            metadata["has_attachment_mention"] = bool(
                re.search(r'attach|enclosed|please find', text, re.IGNORECASE)
            )
        
        return metadata


# ============================================================================
# KNOWLEDGE SEARCHER
# ============================================================================

class KnowledgeSearcher:
    """Searches product documentation using simple TF-IDF"""

    def __init__(self, docs_path: str = "context/product-docs.md", 
                 company_path: str = "context/company-profile.md"):
        """Load and chunk knowledge base"""
        self.chunks = []
        self._load_documents(docs_path, company_path)

    def _load_documents(self, docs_path: str, company_path: str) -> None:
        """Load and chunk documents"""
        docs = []
        
        # Load product docs
        if os.path.exists(docs_path):
            with open(docs_path, 'r', encoding='utf-8') as f:
                docs.append({"source": "product-docs.md", "content": f.read()})
        
        # Load company profile
        if os.path.exists(company_path):
            with open(company_path, 'r', encoding='utf-8') as f:
                docs.append({"source": "company-profile.md", "content": f.read()})
        
        # Chunk documents by section (split on ## headers)
        for doc in docs:
            sections = re.split(r'\n## ', doc['content'])
            for i, section in enumerate(sections):
                chunk = {
                    "source": doc["source"],
                    "section": i,
                    "content": section[:500],  # Limit chunk size
                    "full_content": section,
                }
                self.chunks.append(chunk)

    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Simple TF-IDF style search
        
        Args:
            query: Search query
            top_k: Number of results to return
            
        Returns:
            List of {chunk, score, source} dicts
        """
        if not query or not self.chunks:
            return []
        
        query_tokens = set(query.lower().split())
        results = []
        
        for chunk in self.chunks:
            content = chunk["full_content"].lower()
            
            # Count matching tokens (simple TF)
            matches = sum(1 for token in query_tokens if token in content)
            
            # Calculate score based on matches and chunk relevance
            score = matches / (len(query_tokens) + 1e-6)
            
            # Boost score for section headers that match
            if query.lower() in chunk["full_content"][:100].lower():
                score *= 1.5
            
            if matches > 0:
                results.append({
                    "chunk": chunk["content"],
                    "full_content": chunk["full_content"],
                    "score": score,
                    "source": chunk["source"],
                })
        
        # Sort by score and return top_k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


# ============================================================================
# SENTIMENT ANALYZER
# ============================================================================

class SentimentAnalyzer:
    """Uses Groq to analyze sentiment"""

    def __init__(self, client: Groq):
        """Initialize with Groq client"""
        self.client = client

    def analyze(self, message: str, history: List[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Analyze sentiment using Groq
        
        Args:
            message: Message to analyze
            history: Conversation history for context
            
        Returns:
            {
                'sentiment': str (positive/neutral/frustrated/angry),
                'score': float (0-1),
                'indicators': list of detected indicators
            }
        """
        history_context = ""
        if history:
            history_context = "\n".join([f"- {m['role']}: {m['content'][:100]}" for m in history[-3:]])

        prompt = f"""Analyze the sentiment of this customer message.

Message: "{message}"

Recent context:
{history_context if history_context else "No prior context"}

Respond ONLY with valid JSON (no markdown, no extra text):
{{
    "sentiment": "positive|neutral|frustrated|angry",
    "score": 0.0-1.0,
    "indicators": ["list", "of", "keywords"]
}}

Be concise. Look for: exclamation marks, ALL CAPS, negative words (angry/frustrated), positive language (positive).
"""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
            )
            
            response_text = response.choices[0].message.content.strip()
            result = json.loads(response_text)
            return result
        except Exception as e:
            # Fallback on error
            print(f"Sentiment analysis error: {e}")
            return {
                "sentiment": "neutral",
                "score": 0.5,
                "indicators": [],
            }


# ============================================================================
# RESPONSE GENERATOR
# ============================================================================

class ResponseGenerator:
    """Generates AI responses using Groq"""

    def __init__(self, client: Groq):
        """Initialize with Groq client"""
        self.client = client

    def generate(self, message: str, context_chunks: List[Dict[str, Any]], 
                 conversation_state: ConversationState, channel: str) -> str:
        """
        Generate response using Groq
        
        Args:
            message: Customer message
            context_chunks: Relevant knowledge base chunks
            conversation_state: Current conversation state
            channel: 'email', 'whatsapp', or 'web'
            
        Returns:
            Generated response text
        """
        # Build context from chunks
        knowledge_context = "\n".join([
            f"- {chunk['source']}: {chunk['chunk']}"
            for chunk in context_chunks
        ])

        # Build conversation history
        history_text = "\n".join([
            f"{msg['role'].title()}: {msg['content']}"
            for msg in conversation_state.messages[-5:]  # Last 5 messages
        ])

        # Nova persona
        system_prompt = """You are Nova, a helpful and professional AI support agent for NovaDeskAI.

PERSONA:
- Friendly, professional, and empathetic
- Patient and thorough
- Solution-focused
- Brand advocate

BRAND VOICE:
- Clear and concise
- Conversational but professional
- Avoids jargon
- Always helpful and supportive

CHANNEL GUIDELINES:
- Email: Professional, complete sentences, thorough
- WhatsApp: Conversational, brief, emoji-friendly
- Web: Semi-formal, direct, with CTAs"""

        user_prompt = f"""Customer Message: {message}

Relevant Knowledge:
{knowledge_context if knowledge_context else "No relevant docs found"}

Conversation History:
{history_text if history_text else "New conversation"}

Channel: {channel}

Respond naturally and helpfully. Keep response under 150 words for WhatsApp, 300 words for others.
If you don't know something, offer to escalate or provide best-guess guidance."""

        try:
            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=400,
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Response generation error: {e}")
            return "I apologize, but I'm having trouble processing your request. Let me escalate this to our team for you."


# ============================================================================
# CHANNEL FORMATTER
# ============================================================================

class ChannelFormatter:
    """Formats responses for different channels"""

    def format(self, response: str, channel: str, customer_name: str = "there") -> str:
        """
        Format response for channel
        
        Args:
            response: Raw response text
            channel: 'email', 'whatsapp', or 'web'
            customer_name: Customer name for greeting
            
        Returns:
            Formatted response
        """
        if channel.lower() == "email":
            return self._format_email(response, customer_name)
        elif channel.lower() == "whatsapp":
            return self._format_whatsapp(response)
        elif channel.lower() == "web":
            return self._format_web(response)
        else:
            return response

    def _format_email(self, response: str, customer_name: str) -> str:
        """Email formatting: greeting + content + signature"""
        # Strip any existing greeting line at the start of response
        # Match patterns like: "Dear...,\n", "Hi...,\n", "Hello...,\n", "Greetings...,\n"
        response = re.sub(r'^(Dear|Hi|Hello|Greetings)[^,]*,\s*\n', '', response, flags=re.IGNORECASE)
        
        greeting = f"Hi {customer_name},\n\n"
        signature = "\n\nBest regards,\nNova | NovaDeskAI Support"
        
        # Ensure full sentences
        if not response.endswith(('.', '!', '?')):
            response += "."
        
        return greeting + response + signature

    def _format_whatsapp(self, response: str) -> str:
        """WhatsApp formatting: truncate if needed, conversational"""
        max_length = 300
        
        if len(response) > max_length:
            truncated = response[:max_length - 3].rsplit(' ', 1)[0]
            response = truncated + "..."
        
        return response

    def _format_web(self, response: str) -> str:
        """Web formatting: semi-formal with CTA"""
        cta = "\n\nNeed more help? Chat with our team →"
        
        # Ensure full sentences
        if not response.endswith(('.', '!', '?')):
            response += "."
        
        return response + cta


# ============================================================================
# ESCALATION ENGINE
# ============================================================================

class EscalationEngine:
    """Manages escalation logic and assignment"""

    ESCALATION_RULES = {
        # (sentiment, failed_attempts, resolution_status) -> (escalate, tier, reason)
    }

    def should_escalate(self, state: ConversationState, 
                       sentiment_result: Dict[str, Any]) -> Dict[str, Any]:
        """
        Determine if conversation should escalate
        
        Args:
            state: Current conversation state
            sentiment_result: Sentiment analysis result
            
        Returns:
            {
                'escalate': bool,
                'tier': int (1, 2, or 3),
                'reason': str
            }
        """
        sentiment = sentiment_result.get("sentiment", "neutral")
        score = sentiment_result.get("score", 0.5)
        
        # Rule: angry sentiment + P1 priority → tier 3
        if sentiment == "angry" and state.metadata.get("priority") == "P1":
            return {
                "escalate": True,
                "tier": 3,
                "reason": "Angry customer with critical priority",
            }
        
        # Rule: angry sentiment → tier 2
        if sentiment == "angry":
            return {
                "escalate": True,
                "tier": 2,
                "reason": "Angry customer detected",
            }
        
        # Rule: frustrated + failed attempts >= 2 → tier 2
        if sentiment == "frustrated" and state.failed_attempts >= 2:
            return {
                "escalate": True,
                "tier": 2,
                "reason": f"Frustrated customer with {state.failed_attempts} failed attempts",
            }
        
        # Rule: failed attempts >= 3 → tier 2
        if state.failed_attempts >= 3:
            return {
                "escalate": True,
                "tier": 2,
                "reason": "Multiple failed resolution attempts",
            }
        
        # Rule: already escalated → stay escalated (tier 2)
        if state.resolution_status == ResolutionStatus.ESCALATED:
            return {
                "escalate": True,
                "tier": 2,
                "reason": "Previously escalated conversation",
            }
        
        # No escalation needed
        return {
            "escalate": False,
            "tier": 1,
            "reason": "No escalation required",
        }

    def escalate(self, state: ConversationState, tier: int, 
                 reason: str) -> Dict[str, Any]:
        """
        Execute escalation
        
        Args:
            state: Conversation state
            tier: Escalation tier (1, 2, 3)
            reason: Escalation reason
            
        Returns:
            Escalation record
        """
        # Determine agent assignment based on tier
        if tier == 1:
            assigned_to = "bot"
        elif tier == 2:
            assigned_to = "agent@novadesk.ai"
        else:  # tier 3
            assigned_to = "senior@novadesk.ai"
        
        # Determine expected response time
        response_times = {1: "2 hours", 2: "30 minutes", 3: "15 minutes"}
        
        escalation_record = {
            "escalation_id": str(uuid.uuid4())[:8],
            "conversation_id": state.conversation_id,
            "customer_id": state.customer_id,
            "tier": tier,
            "reason": reason,
            "assigned_to": assigned_to,
            "expected_response_time": response_times[tier],
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # Update conversation state
        state.resolution_status = ResolutionStatus.ESCALATED
        state.updated_at = datetime.now(timezone.utc).isoformat()
        state.metadata["escalation_tier"] = tier
        
        return escalation_record


# ============================================================================
# AGENT LOOP (MAIN ORCHESTRATOR)
# ============================================================================

class AgentLoop:
    """Main orchestrator for the agent loop"""

    def __init__(self):
        """Initialize all components"""
        # Initialize Groq client
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            print("WARNING: GROQ_API_KEY not set. Using mock mode.")
            self.client = None
        else:
            self.client = Groq(api_key=api_key)
        
        # Initialize components
        self.normalizer = MessageNormalizer()
        self.knowledge_searcher = KnowledgeSearcher()
        self.sentiment_analyzer = SentimentAnalyzer(self.client) if self.client else None
        self.response_generator = ResponseGenerator(self.client) if self.client else None
        self.channel_formatter = ChannelFormatter()
        self.escalation_engine = EscalationEngine()
        
        # In-memory conversation store
        self.conversations: Dict[str, ConversationState] = {}

    def process_message(self, message: str, channel: str, customer_id: str,
                       conversation_id: str = None) -> Dict[str, Any]:
        """
        Main agent loop: process customer message and generate response
        
        Args:
            message: Customer message
            channel: 'email', 'whatsapp', or 'web'
            customer_id: Customer identifier
            conversation_id: Optional existing conversation ID
            
        Returns:
            {
                'response': str (raw),
                'formatted_response': str (channel-specific),
                'conversation_id': str,
                'escalated': bool,
                'escalation_details': dict or None,
                'sentiment': str,
                'channel': str,
                'topics': list,
            }
        """
        # 1. Get or create ConversationState
        if conversation_id and conversation_id in self.conversations:
            state = self.conversations[conversation_id]
        else:
            conversation_id = str(uuid.uuid4())
            state = ConversationState(
                conversation_id=conversation_id,
                customer_id=customer_id,
                channel=channel,
            )
            self.conversations[conversation_id] = state

        # 2. Normalize message
        normalized = self.normalizer.normalize(message, channel)

        # 3. Analyze sentiment
        sentiment_result = None
        if self.sentiment_analyzer:
            sentiment_result = self.sentiment_analyzer.analyze(
                normalized["normalized_text"], state.messages
            )
            state.sentiment = sentiment_result.get("sentiment", "neutral")
        else:
            sentiment_result = {"sentiment": "neutral", "score": 0.5, "indicators": []}

        # Extract topics from indicators
        topics = sentiment_result.get("indicators", [])
        state.topics.extend(topics)
        state.topics = list(set(state.topics))  # Deduplicate

        # 4. Search knowledge base
        context_chunks = self.knowledge_searcher.search(
            normalized["normalized_text"], top_k=3
        )

        # 5. Generate response
        if self.response_generator:
            raw_response = self.response_generator.generate(
                normalized["normalized_text"],
                context_chunks,
                state,
                channel,
            )
        else:
            raw_response = "Thank you for contacting NovaDeskAI. I'm having trouble accessing the AI service right now."

        # 6. Format per channel
        formatted_response = self.channel_formatter.format(
            raw_response, channel, state.metadata.get("customer_name", "there")
        )

        # 7. Check escalation
        escalation_decision = self.escalation_engine.should_escalate(
            state, sentiment_result
        )
        escalation_details = None
        if escalation_decision["escalate"]:
            escalation_details = self.escalation_engine.escalate(
                state, escalation_decision["tier"], escalation_decision["reason"]
            )

        # 8. Update state
        state.messages.append({"role": "user", "content": normalized["normalized_text"]})
        state.messages.append({"role": "assistant", "content": raw_response})
        
        if state.resolution_status == ResolutionStatus.OPEN:
            state.resolution_status = ResolutionStatus.IN_PROGRESS
        
        state.updated_at = datetime.now(timezone.utc).isoformat()

        # 9. Return result
        return {
            "response": raw_response,
            "formatted_response": formatted_response,
            "conversation_id": conversation_id,
            "escalated": escalation_decision["escalate"],
            "escalation_details": escalation_details,
            "sentiment": state.sentiment,
            "channel": channel,
            "topics": state.topics,
        }

    def get_conversation(self, conversation_id: str) -> Optional[ConversationState]:
        """Retrieve conversation state by ID"""
        return self.conversations.get(conversation_id)


# ============================================================================
# MAIN & DEMO
# ============================================================================

def main():
    """Demo run with 3 test messages (one per channel)"""
    
    print("=" * 80)
    print("NovaDeskAI - Customer Success Agent Prototype")
    print("=" * 80)
    print()

    # Initialize agent
    agent = AgentLoop()

    # Test messages
    test_cases = [
        {
            "message": "Hi, I forgot my password and can't log into my account. I've tried the reset link but it's not working. This is really frustrating!",
            "channel": "email",
            "customer_id": "cust_001",
            "name": "John Smith",
        },
        {
            "message": "hey, i want to know about pricing 😊 is there a free trial?",
            "channel": "whatsapp",
            "customer_id": "cust_002",
            "name": "Maria",
        },
        {
            "message": "I have a billing question about my recent invoice. Can you help?",
            "channel": "web",
            "customer_id": "cust_003",
            "name": "Alex",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'=' * 80}")
        print(f"TEST CASE {i}: {test_case['channel'].upper()}")
        print(f"{'=' * 80}")
        print()

        # Set customer name in metadata
        message = test_case["message"]
        channel = test_case["channel"]
        customer_id = test_case["customer_id"]
        customer_name = test_case["name"]

        # Mock the agent to add customer name
        print(f"Customer: {customer_name}")
        print(f"Channel: {channel.upper()}")
        print(f"Message: {message}")
        print()

        # Process message
        result = agent.process_message(message, channel, customer_id)
        
        # Get conversation and set name
        conv = agent.get_conversation(result["conversation_id"])
        if conv:
            conv.metadata["customer_name"] = customer_name

        print("=" * 40)
        print("AGENT ANALYSIS:")
        print("=" * 40)
        print(f"Sentiment: {result['sentiment']}")
        print(f"Topics: {', '.join(result['topics']) if result['topics'] else 'None'}")
        print(f"Escalated: {result['escalated']}")
        
        if result["escalation_details"]:
            details = result["escalation_details"]
            print(f"Escalation Tier: {details['tier']}")
            print(f"Reason: {details['reason']}")
            print(f"Assigned To: {details['assigned_to']}")
            print(f"Expected Response: {details['expected_response_time']}")
        
        print()
        print("=" * 40)
        print("RAW RESPONSE:")
        print("=" * 40)
        print(result["response"])
        print()
        print("=" * 40)
        print(f"FORMATTED RESPONSE ({channel.upper()}):")
        print("=" * 40)
        print(result["formatted_response"])
        print()

    print("\n" + "=" * 80)
    print("Demo completed!")
    print("=" * 80)


if __name__ == "__main__":
    main()

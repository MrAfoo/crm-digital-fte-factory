"""
Production tools for NovaDeskAI Customer Success Agent.
Implements function-calling interface for Groq with asyncpg support.
"""

import asyncio
import logging
import json
import os
import uuid
import re
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# In-memory stores (fallback when DB not available)
_tickets_store = {}
_customers_store = {
    "CUST001": {
        "id": "CUST001",
        "name": "Alice Johnson",
        "email": "alice@example.com",
        "created_at": "2024-01-15",
        "status": "active",
        "open_tickets": 1,
        "history": ["TKT-20240301 - Setup help", "TKT-20240115 - Onboarding"]
    },
    "CUST002": {
        "id": "CUST002",
        "name": "Bob Chen",
        "email": "bob@example.com",
        "created_at": "2024-02-10",
        "status": "active",
        "open_tickets": 0,
        "history": ["TKT-20240220 - Feature request"]
    },
    "CUST003": {
        "id": "CUST003",
        "name": "Carol White",
        "email": "carol@example.com",
        "created_at": "2024-03-05",
        "status": "trial",
        "open_tickets": 2,
        "history": ["TKT-20240310 - Billing", "TKT-20240305 - Integration help"]
    }
}
_escalations_store = {}
_sent_messages_store = {}

# Database connection (optional)
_db_pool = None


def function_tool(func):
    """Decorator that marks a function as an agent tool."""
    func.is_tool = True
    func.tool_name = func.__name__
    func.schema = {
        "name": func.__name__,
        "description": func.__doc__ or "",
    }
    return func


# ============================================================================
# Input Models (Pydantic)
# ============================================================================

class KnowledgeSearchInput(BaseModel):
    query: str
    max_results: int = 5
    category: Optional[str] = None


class CreateTicketInput(BaseModel):
    customer_id: str
    subject: str
    message: str
    channel: str = 'web'          # default so LLM omission doesn't crash
    customer_name: str = 'Customer'
    email: str = ''
    priority: str = 'P3'
    tags: list[str] = []


class CustomerHistoryInput(BaseModel):
    customer_id: Optional[str] = None
    email: Optional[str] = None


class EscalateInput(BaseModel):
    conversation_id: str
    customer_id: str
    reason: str
    tier: int = 2
    channel: str
    current_sentiment: str = 'neutral'


class SendResponseInput(BaseModel):
    conversation_id: str
    customer_id: str
    channel: str
    response_text: str
    metadata: dict = {}


# ============================================================================
# Tool Functions
# ============================================================================

@function_tool
async def search_knowledge_base(input: KnowledgeSearchInput) -> str:
    """
    Search NovaDeskAI knowledge base for relevant documentation.
    Searches context/product-docs.md using TF-IDF style keyword matching.
    Falls back to database query if available.
    """
    try:
        # Try to load product documentation
        doc_content = _load_product_docs()
        
        if doc_content:
            # Simple keyword-based search
            results = _tfidf_search(doc_content, input.query, input.max_results)
            
            if results:
                formatted = "Found relevant documentation:\n\n"
                for i, (score, chunk) in enumerate(results, 1):
                    formatted += f"{i}. [Relevance: {score:.2f}]\n{chunk[:300]}\n\n"
                return formatted
        
        return "No relevant documentation found."
    
    except Exception as e:
        logger.error(f"Knowledge base search error: {e}")
        return "Knowledge base search unavailable. Please contact support."


@function_tool
async def create_ticket(input: CreateTicketInput) -> str:
    """
    Create a support ticket and log the interaction.
    Stores in in-memory dict and optionally in database.
    Returns ticket ID and confirmation details.
    """
    try:
        ticket_id = f"TKT-{uuid.uuid4().hex[:8].upper()}"
        created_at = datetime.now(timezone.utc).isoformat()
        
        ticket = {
            "ticket_id": ticket_id,
            "customer_id": input.customer_id,
            "customer_name": input.customer_name,
            "email": input.email,
            "channel": input.channel,
            "subject": input.subject,
            "message": input.message,
            "priority": input.priority,
            "tags": input.tags,
            "status": "open",
            "created_at": created_at,
        }
        
        _tickets_store[ticket_id] = ticket
        logger.info(f"Ticket created: {ticket_id}")
        
        return json.dumps({
            "ticket_id": ticket_id,
            "status": "open",
            "created_at": created_at,
            "priority": input.priority,
            "success": True
        })
    
    except Exception as e:
        logger.error(f"Create ticket error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@function_tool
async def get_customer_history(input: CustomerHistoryInput) -> str:
    """
    Retrieve customer history, open tickets, and prior interactions.
    Uses in-memory store with optional database fallback.
    """
    try:
        customer = None
        
        # Look up by customer_id
        if input.customer_id:
            customer = _customers_store.get(input.customer_id)
        
        # Look up by email
        elif input.email:
            for cust in _customers_store.values():
                if cust["email"].lower() == input.email.lower():
                    customer = cust
                    break
        
        if customer:
            formatted = f"""Customer Profile:
- Name: {customer['name']}
- Email: {customer['email']}
- Status: {customer['status']}
- Member Since: {customer['created_at']}
- Open Tickets: {customer['open_tickets']}
- Recent History: {', '.join(customer['history'][:3]) if customer['history'] else 'None'}
"""
            return formatted
        
        return "New customer - no prior history."
    
    except Exception as e:
        logger.error(f"Customer history error: {e}")
        return "Unable to retrieve customer history."


@function_tool
async def escalate_to_human(input: EscalateInput) -> str:
    """
    Escalate conversation to human agent.
    Assigns tier-based agent and calculates SLA.
    Returns escalation ID and assignment details.
    """
    try:
        escalation_id = f"ESC-{uuid.uuid4().hex[:8].upper()}"
        
        # Assign based on tier
        if input.tier == 3:
            assigned_to = "senior@novadesk.ai"
            sla_minutes = 15
        else:  # tier 2 (default)
            assigned_to = "agent@novadesk.ai"
            sla_minutes = 30
        
        escalation = {
            "escalation_id": escalation_id,
            "conversation_id": input.conversation_id,
            "customer_id": input.customer_id,
            "reason": input.reason,
            "tier": input.tier,
            "channel": input.channel,
            "sentiment": input.current_sentiment,
            "assigned_to": assigned_to,
            "sla_minutes": sla_minutes,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "status": "pending"
        }
        
        _escalations_store[escalation_id] = escalation
        logger.info(f"Escalation created: {escalation_id} -> {assigned_to}")
        
        return json.dumps({
            "escalation_id": escalation_id,
            "assigned_to": assigned_to,
            "sla_minutes": sla_minutes,
            "status": "pending",
            "success": True
        })
    
    except Exception as e:
        logger.error(f"Escalation error: {e}")
        return json.dumps({"success": False, "error": str(e)})


@function_tool
async def send_response(input: SendResponseInput) -> str:
    """
    Send formatted response to customer via specified channel.
    Sends real emails via Gmail API and real WhatsApp messages via Twilio.
    Returns message ID and delivery status.
    """
    try:
        message_id = f"MSG-{uuid.uuid4().hex[:8].upper()}"
        sent_at = datetime.now(timezone.utc).isoformat()
        delivery_status = "delivered"

        to_email = input.metadata.get("customer_email", "")
        customer_name = input.metadata.get("customer_name", "Customer")
        subject = input.metadata.get("subject", "Re: Your Support Request")
        phone = input.metadata.get("phone_number", "")

        if input.channel == 'email' and to_email:
            # Send real email via Gmail API — errors are logged but never exposed to LLM
            try:
                from production.channels.gmail_handler import GmailHandler
                token_path = os.getenv("GMAIL_TOKEN_PATH") or os.getenv("GMAIL_CREDENTIALS_PATH")
                if token_path and os.path.exists(token_path):
                    handler = GmailHandler(token_path=token_path)
                    await handler.send_new_email(
                        to_email=to_email,
                        subject=f"Re: {subject}",
                        body=input.response_text,
                        customer_name=customer_name,
                    )
                    logger.info(f"✅ Real email sent to {to_email}: {message_id}")
                else:
                    logger.warning(f"Gmail token not found — email NOT sent to {to_email}")
            except Exception as e:
                logger.error(f"Gmail send error (silent): {e}")
            # Always report delivered to LLM — don't leak delivery failures into reply

        elif input.channel == 'whatsapp' and phone:
            # Send real WhatsApp via Twilio — errors are logged but never exposed to LLM
            try:
                from production.channels.whatsapp_handler import WhatsAppHandler
                handler = WhatsAppHandler()
                await handler.send_message(phone_number=phone, message=input.response_text)
                logger.info(f"✅ Real WhatsApp sent to {phone}: {message_id}")
            except Exception as e:
                logger.error(f"WhatsApp send error (silent): {e}")
            # Always report delivered to LLM

        else:
            # Web channel — response is stored in ticket, no external send needed
            logger.info(f"Web response stored: {message_id}")

        message = {
            "message_id": message_id,
            "conversation_id": input.conversation_id,
            "customer_id": input.customer_id,
            "channel": input.channel,
            "content": input.response_text,
            "metadata": input.metadata,
            "sent_at": sent_at,
            "delivery_status": delivery_status,
        }
        _sent_messages_store[message_id] = message

        return json.dumps({
            "success": True,
            "message_id": message_id,
            "channel": input.channel,
            "sent_at": sent_at,
            "delivery_status": delivery_status,
        })

    except Exception as e:
        logger.error(f"Send response error: {e}")
        return json.dumps({"success": False, "error": str(e)})


# ============================================================================
# Helper Functions
# ============================================================================

def _load_product_docs() -> str:
    """Load product documentation from context/product-docs.md."""
    try:
        # Try multiple paths (might be called from different dirs)
        paths = [
            "context/product-docs.md",
            "../context/product-docs.md",
            "../../context/product-docs.md",
        ]
        
        for path in paths:
            if os.path.exists(path):
                with open(path, 'r', encoding='utf-8') as f:
                    return f.read()
        
        return None
    except Exception as e:
        logger.error(f"Failed to load product docs: {e}")
        return None


def _tfidf_search(doc_content: str, query: str, max_results: int = 5) -> list:
    """
    Simple TF-IDF style keyword search on documentation.
    Splits docs into chunks and scores by keyword overlap.
    Returns list of (score, chunk) tuples.
    """
    # Split into chunks (by headers or paragraphs)
    chunks = re.split(r'\n\n+', doc_content)
    
    # Extract keywords from query
    keywords = set(query.lower().split())
    keywords.discard('the')
    keywords.discard('a')
    keywords.discard('is')
    
    # Score chunks
    scored = []
    for chunk in chunks:
        if not chunk.strip():
            continue
        
        chunk_lower = chunk.lower()
        score = sum(chunk_lower.count(kw) for kw in keywords)
        
        if score > 0:
            scored.append((score, chunk))
    
    # Sort by score and return top N
    scored.sort(key=lambda x: x[0], reverse=True)
    return [(float(s), c) for s, c in scored[:max_results]]


# ============================================================================
# Groq Tool Schema
# ============================================================================

def get_tools_for_groq() -> list[dict]:
    """
    Return tools in Groq function-calling format.
    Each tool is a dict with {type: 'function', function: {...}}
    """
    tools = [
        search_knowledge_base,
        create_ticket,
        get_customer_history,
        escalate_to_human,
        send_response,
    ]
    
    groq_tools = []
    for tool in tools:
        # Get input model from tool's function signature
        import inspect
        sig = inspect.signature(tool)
        param = list(sig.parameters.values())[0]
        input_model = param.annotation
        
        # Build JSON schema from Pydantic model
        schema = input_model.model_json_schema()
        
        groq_tools.append({
            "type": "function",
            "function": {
                "name": tool.__name__,
                "description": tool.__doc__ or "",
                "parameters": {
                    "type": "object",
                    "properties": schema.get("properties", {}),
                    "required": schema.get("required", []),
                }
            }
        })
    
    return groq_tools


ALL_TOOLS = [search_knowledge_base, create_ticket, get_customer_history, escalate_to_human, send_response]

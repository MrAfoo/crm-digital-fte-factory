from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Dict
from datetime import datetime
import uuid
import random
import string
import json

app = FastAPI(
    title="NovaDeskAI API",
    description="Customer Success AI Agent Backend",
    version="1.0.0"
)

# CORS configuration - allow all origins for web form embedding
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# Pydantic Models
# ============================================================================

class TicketCreateRequest(BaseModel):
    """Request model for creating a support ticket"""
    name: str = Field(..., min_length=1, max_length=255)
    email: EmailStr
    subject: str = Field(..., min_length=1, max_length=500)
    channel: str = Field(..., pattern="^(Web|Email|WhatsApp)$")
    description: str = Field(..., min_length=20, max_length=1000)


class TicketResponse(BaseModel):
    """Response model for ticket creation"""
    ticket_id: str
    status: str
    message: str
    estimated_response_time: str
    created_at: str


class Ticket(BaseModel):
    """Complete ticket model"""
    ticket_id: str
    name: str
    email: str
    subject: str
    channel: str
    description: str
    status: str
    priority: str
    created_at: str
    updated_at: str


class TicketList(BaseModel):
    """Response model for ticket listing"""
    tickets: List[Ticket]
    total: int


class TicketStatusUpdate(BaseModel):
    """Request model for updating ticket status"""
    status: str = Field(..., pattern="^(open|in_progress|resolved|escalated)$")


class MessageProcessRequest(BaseModel):
    """Request model for processing a message through the agent"""
    message: str = Field(..., min_length=1, max_length=2000)
    channel: str = Field(..., pattern="^(Web|Email|WhatsApp)$")
    customer_id: str
    conversation_id: Optional[str] = None


class MessageProcessResponse(BaseModel):
    """Response model for message processing"""
    response: str
    conversation_id: str
    agent_action: str
    confidence: float
    requires_escalation: bool


class ConversationState(BaseModel):
    """Response model for conversation state"""
    conversation_id: str
    customer_id: str
    status: str
    messages: List[Dict]
    created_at: str
    updated_at: str


class HealthCheck(BaseModel):
    """Health check response"""
    status: str
    version: str
    timestamp: str


class StatsResponse(BaseModel):
    """Dashboard statistics response"""
    total_tickets: int
    by_status: Dict[str, int]
    by_channel: Dict[str, int]
    by_priority: Dict[str, int]
    avg_response_time: str


# ============================================================================
# In-Memory Storage
# ============================================================================

tickets_db: Dict[str, Dict] = {}
conversations_db: Dict[str, Dict] = {}


def generate_ticket_id() -> str:
    """Generate ticket ID in format TKT-XXXX"""
    random_num = random.randint(1000, 9999)
    return f"TKT-{random_num}"


def create_sample_tickets():
    """Pre-seed database with 5 sample tickets"""
    sample_data = [
        {
            "name": "Alice Johnson",
            "email": "alice@example.com",
            "subject": "Login issue with my account",
            "channel": "Email",
            "description": "I am unable to log into my account. I have tried resetting my password multiple times but still cannot access the system. Please help me regain access to my account immediately.",
            "priority": "high",
            "status": "in_progress"
        },
        {
            "name": "Bob Smith",
            "email": "bob@example.com",
            "subject": "Billing inquiry",
            "channel": "Web",
            "description": "I was charged twice for my subscription this month. Can you please review my billing history and refund the duplicate charge? I have attached my invoice reference number to this ticket.",
            "priority": "high",
            "status": "open"
        },
        {
            "name": "Carol Martinez",
            "email": "carol@example.com",
            "subject": "Feature request for dashboard",
            "channel": "WhatsApp",
            "description": "I would like to request a new feature that allows exporting reports in PDF format. This would greatly improve our workflow and save us time on manual document creation.",
            "priority": "low",
            "status": "open"
        },
        {
            "name": "David Lee",
            "email": "david@example.com",
            "subject": "API integration error",
            "channel": "Email",
            "description": "Our development team is experiencing issues integrating with your API. We are getting authentication errors even with valid credentials. Our integration deadline is next week, so this is urgent.",
            "priority": "critical",
            "status": "in_progress"
        },
        {
            "name": "Emma Wilson",
            "email": "emma@example.com",
            "subject": "Performance issue - slow response time",
            "channel": "Web",
            "description": "The platform has been running very slowly over the past two days. Page loads take 10+ seconds and reports take forever to generate. This is impacting our daily operations significantly.",
            "priority": "high",
            "status": "resolved"
        }
    ]

    for sample in sample_data:
        ticket_id = generate_ticket_id()
        now = datetime.utcnow().isoformat()
        tickets_db[ticket_id] = {
            "ticket_id": ticket_id,
            "name": sample["name"],
            "email": sample["email"],
            "subject": sample["subject"],
            "channel": sample["channel"],
            "description": sample["description"],
            "status": sample["status"],
            "priority": sample["priority"],
            "created_at": now,
            "updated_at": now
        }


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_stats():
    """Calculate dashboard statistics"""
    stats = {
        "total_tickets": len(tickets_db),
        "by_status": {"open": 0, "in_progress": 0, "resolved": 0, "escalated": 0},
        "by_channel": {"Web": 0, "Email": 0, "WhatsApp": 0},
        "by_priority": {"low": 0, "medium": 0, "high": 0, "critical": 0}
    }

    for ticket in tickets_db.values():
        status = ticket.get("status", "open")
        channel = ticket.get("channel", "Web")
        priority = ticket.get("priority", "medium")

        if status in stats["by_status"]:
            stats["by_status"][status] += 1
        if channel in stats["by_channel"]:
            stats["by_channel"][channel] += 1
        if priority in stats["by_priority"]:
            stats["by_priority"][priority] += 1

    return stats


def get_agent_response(message: str, channel: str) -> Dict:
    """
    Process message through agent if available, else return mock response.
    Attempts to import and use AgentLoop from src.agent.prototype
    """
    try:
        from src.agent.prototype import AgentLoop
        agent = AgentLoop()
        response = agent.process(message, channel)
        return {
            "response": response.get("text", "Thank you for your message."),
            "agent_action": response.get("action", "respond"),
            "confidence": response.get("confidence", 0.95),
            "requires_escalation": response.get("requires_escalation", False)
        }
    except (ImportError, AttributeError, Exception):
        # Fallback to mock response if agent not available
        responses = {
            "Web": "Thank you for contacting NovaDeskAI. A support specialist will assist you shortly.",
            "Email": "We have received your message and will respond within 2 hours.",
            "WhatsApp": "Hi! Thanks for reaching out. Our team will get back to you soon!"
        }
        return {
            "response": responses.get(channel, "Thank you for your message."),
            "agent_action": "respond",
            "confidence": 0.85,
            "requires_escalation": False
        }


# ============================================================================
# API Endpoints
# ============================================================================

@app.post("/api/tickets", response_model=TicketResponse)
async def create_ticket(request: TicketCreateRequest):
    """
    Submit a support ticket from the web form.
    
    - **name**: Customer's full name
    - **email**: Customer's email address
    - **subject**: Support ticket subject
    - **channel**: Preferred communication channel (Web, Email, WhatsApp)
    - **description**: Detailed issue description (20-1000 chars)
    """
    ticket_id = generate_ticket_id()
    now = datetime.utcnow().isoformat()

    # Determine priority based on keywords
    priority = "medium"
    urgent_keywords = ["urgent", "critical", "asap", "emergency", "down", "broken"]
    if any(keyword in request.description.lower() for keyword in urgent_keywords):
        priority = "high"

    ticket_data = {
        "ticket_id": ticket_id,
        "name": request.name,
        "email": request.email,
        "subject": request.subject,
        "channel": request.channel,
        "description": request.description,
        "status": "open",
        "priority": priority,
        "created_at": now,
        "updated_at": now
    }

    tickets_db[ticket_id] = ticket_data

    return TicketResponse(
        ticket_id=ticket_id,
        status="open",
        message="Your support ticket has been created successfully.",
        estimated_response_time="< 2 minutes",
        created_at=now
    )


@app.get("/api/tickets", response_model=TicketList)
async def list_tickets(status: Optional[str] = Query(None, pattern="^(open|in_progress|resolved|escalated)$")):
    """
    List all tickets with optional status filter.
    
    - **status** (optional): Filter by status (open, in_progress, resolved, escalated)
    """
    tickets = list(tickets_db.values())

    if status:
        tickets = [t for t in tickets if t.get("status") == status]

    # Sort by creation date (newest first)
    tickets.sort(key=lambda x: x.get("created_at", ""), reverse=True)

    return TicketList(
        tickets=[Ticket(**t) for t in tickets],
        total=len(tickets)
    )


@app.get("/api/tickets/{ticket_id}", response_model=Ticket)
async def get_ticket(ticket_id: str):
    """
    Get details of a specific ticket.
    
    - **ticket_id**: The ticket ID (e.g., TKT-1234)
    """
    if ticket_id not in tickets_db:
        raise HTTPException(status_code=404, detail="Ticket not found")

    return Ticket(**tickets_db[ticket_id])


@app.put("/api/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: str, request: TicketStatusUpdate):
    """
    Update the status of a ticket.
    
    - **ticket_id**: The ticket ID (e.g., TKT-1234)
    - **status**: New status (open, in_progress, resolved, escalated)
    """
    if ticket_id not in tickets_db:
        raise HTTPException(status_code=404, detail="Ticket not found")

    tickets_db[ticket_id]["status"] = request.status
    tickets_db[ticket_id]["updated_at"] = datetime.utcnow().isoformat()

    return {
        "success": True,
        "message": f"Ticket {ticket_id} status updated to {request.status}",
        "ticket": Ticket(**tickets_db[ticket_id])
    }


@app.post("/api/messages/process", response_model=MessageProcessResponse)
async def process_message(request: MessageProcessRequest):
    """
    Process a message through the AI agent.
    
    - **message**: The customer message to process
    - **channel**: Communication channel (Web, Email, WhatsApp)
    - **customer_id**: Customer identifier
    - **conversation_id** (optional): Existing conversation ID
    """
    conversation_id = request.conversation_id or str(uuid.uuid4())

    # Get agent response
    agent_result = get_agent_response(request.message, request.channel)

    # Store conversation if not exists
    if conversation_id not in conversations_db:
        conversations_db[conversation_id] = {
            "conversation_id": conversation_id,
            "customer_id": request.customer_id,
            "status": "active",
            "messages": [],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat()
        }

    # Add message to conversation
    conversations_db[conversation_id]["messages"].append({
        "role": "customer",
        "message": request.message,
        "timestamp": datetime.utcnow().isoformat()
    })

    conversations_db[conversation_id]["messages"].append({
        "role": "agent",
        "message": agent_result["response"],
        "timestamp": datetime.utcnow().isoformat()
    })

    conversations_db[conversation_id]["updated_at"] = datetime.utcnow().isoformat()

    return MessageProcessResponse(
        response=agent_result["response"],
        conversation_id=conversation_id,
        agent_action=agent_result["agent_action"],
        confidence=agent_result["confidence"],
        requires_escalation=agent_result["requires_escalation"]
    )


@app.get("/api/conversations/{conversation_id}", response_model=ConversationState)
async def get_conversation(conversation_id: str):
    """
    Get the state of a conversation.
    
    - **conversation_id**: The conversation ID
    """
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")

    return ConversationState(**conversations_db[conversation_id])


@app.get("/api/health", response_model=HealthCheck)
async def health_check():
    """
    Health check endpoint with version info.
    """
    return HealthCheck(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.utcnow().isoformat()
    )


@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """
    Get dashboard statistics about tickets and conversations.
    
    Returns:
    - Total number of tickets
    - Tickets grouped by status
    - Tickets grouped by channel
    - Tickets grouped by priority
    - Average response time
    """
    stats = calculate_stats()

    return StatsResponse(
        total_tickets=stats["total_tickets"],
        by_status=stats["by_status"],
        by_channel=stats["by_channel"],
        by_priority=stats["by_priority"],
        avg_response_time="< 2 minutes"
    )


# ============================================================================
# Startup and Main
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize sample data on startup"""
    create_sample_tickets()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

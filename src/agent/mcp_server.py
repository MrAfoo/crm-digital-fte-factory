"""
NovaDeskAI MCP (Model Context Protocol) Server
Exposes 5 tools as REST endpoints for knowledge retrieval, ticketing, escalation, and messaging.
"""

import os
import uuid
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from enum import Enum

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import uvicorn


# ============================================================================
# DATA MODELS (Pydantic)
# ============================================================================

class SearchKnowledgeBaseRequest(BaseModel):
    """Request model for knowledge base search"""
    query: str
    channel: str = "web"
    top_k: int = Field(default=3, ge=1, le=10)


class SearchKnowledgeBaseResponse(BaseModel):
    """Response model for knowledge base search"""
    results: List[Dict[str, Any]]
    total_found: int
    query: str


class CreateTicketRequest(BaseModel):
    """Request model for ticket creation"""
    customer_id: str
    customer_name: str
    email: str
    channel: str  # email, whatsapp, web
    subject: str
    message: str
    priority: str = "P3"  # P1, P2, P3
    tags: List[str] = Field(default_factory=list)


class CreateTicketResponse(BaseModel):
    """Response model for ticket creation"""
    ticket_id: str
    status: str
    created_at: str
    priority: str
    message: str


class CustomerHistoryRequest(BaseModel):
    """Request model for customer history lookup"""
    customer_id: Optional[str] = None
    email: Optional[str] = None


class CustomerHistoryResponse(BaseModel):
    """Response model for customer history"""
    customer_id: str
    customer_name: str
    email: str
    tier: str
    open_tickets: List[Dict[str, Any]]
    resolved_tickets: List[Dict[str, Any]]
    total_tickets: int
    avg_sentiment: str
    last_contact: Optional[str]


class EscalateRequest(BaseModel):
    """Request model for escalation"""
    conversation_id: str
    customer_id: str
    reason: str
    tier: int = 2  # 1, 2, or 3
    channel: str
    current_sentiment: str


class EscalateResponse(BaseModel):
    """Response model for escalation"""
    escalation_id: str
    assigned_to: str
    expected_response_time: str
    ticket_id: str
    message: str


class SendResponseRequest(BaseModel):
    """Request model for sending response"""
    conversation_id: str
    customer_id: str
    channel: str
    response_text: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class SendResponseResponse(BaseModel):
    """Response model for sending response"""
    success: bool
    message_id: str
    channel: str
    sent_at: str
    delivery_status: str


# ============================================================================
# DATA STORES (In-Memory)
# ============================================================================

tickets_db: Dict[str, Dict[str, Any]] = {}
customers_db: Dict[str, Dict[str, Any]] = {
    "cust_001": {
        "customer_id": "cust_001",
        "customer_name": "John Smith",
        "email": "john@example.com",
        "tier": "standard",
        "created_at": (datetime.utcnow() - timedelta(days=180)).isoformat(),
        "last_contact": (datetime.utcnow() - timedelta(days=5)).isoformat(),
    },
    "cust_002": {
        "customer_id": "cust_002",
        "customer_name": "Jane Doe",
        "email": "jane@example.com",
        "tier": "premium",
        "created_at": (datetime.utcnow() - timedelta(days=365)).isoformat(),
        "last_contact": (datetime.utcnow() - timedelta(days=1)).isoformat(),
    },
    "cust_003": {
        "customer_id": "cust_003",
        "customer_name": "Bob Johnson",
        "email": "bob@example.com",
        "tier": "enterprise",
        "created_at": (datetime.utcnow() - timedelta(days=90)).isoformat(),
        "last_contact": datetime.utcnow().isoformat(),
    },
}
escalations_db: Dict[str, Dict[str, Any]] = {}
sent_messages_db: Dict[str, Dict[str, Any]] = {}


# ============================================================================
# KNOWLEDGE BASE LOADER
# ============================================================================

class KnowledgeBase:
    """Simple knowledge base manager"""
    
    def __init__(self):
        self.chunks = []
        self._load()
    
    def _load(self):
        """Load product docs into memory"""
        docs_path = "context/product-docs.md"
        if os.path.exists(docs_path):
            with open(docs_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split by headers
            sections = content.split("\n## ")
            for i, section in enumerate(sections):
                self.chunks.append({
                    "section": i,
                    "content": section[:300],
                    "full_content": section,
                })
    
    def search(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """Search knowledge base"""
        if not query or not self.chunks:
            return []
        
        query_lower = query.lower()
        results = []
        
        for chunk in self.chunks:
            content = chunk["full_content"].lower()
            
            # Count matching keywords
            matches = sum(1 for word in query_lower.split() if word in content)
            
            # Score based on matches
            score = matches / (len(query_lower.split()) + 1e-6)
            
            if matches > 0:
                results.append({
                    "content": chunk["content"],
                    "score": score,
                    "source": "product-docs.md",
                })
        
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]


kb = KnowledgeBase()


# ============================================================================
# MCP TOOL REGISTRY
# ============================================================================

TOOLS_REGISTRY = {
    "search_knowledge_base": {
        "name": "search_knowledge_base",
        "description": "Search the product knowledge base for relevant information",
        "endpoint": "/tools/search_knowledge_base",
        "method": "POST",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "channel": {"type": "string", "description": "Channel context (email, whatsapp, web)"},
                "top_k": {"type": "integer", "description": "Number of results to return"},
            },
            "required": ["query"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "results": {"type": "array"},
                "total_found": {"type": "integer"},
                "query": {"type": "string"},
            },
        },
    },
    "create_ticket": {
        "name": "create_ticket",
        "description": "Create a support ticket for a customer",
        "endpoint": "/tools/create_ticket",
        "method": "POST",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "customer_name": {"type": "string"},
                "email": {"type": "string"},
                "channel": {"type": "string"},
                "subject": {"type": "string"},
                "message": {"type": "string"},
                "priority": {"type": "string", "enum": ["P1", "P2", "P3"]},
                "tags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["customer_id", "customer_name", "email", "channel", "subject", "message"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "ticket_id": {"type": "string"},
                "status": {"type": "string"},
                "created_at": {"type": "string"},
                "priority": {"type": "string"},
                "message": {"type": "string"},
            },
        },
    },
    "get_customer_history": {
        "name": "get_customer_history",
        "description": "Retrieve customer history and ticket information",
        "endpoint": "/tools/get_customer_history",
        "method": "POST",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "email": {"type": "string"},
            },
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "customer_id": {"type": "string"},
                "customer_name": {"type": "string"},
                "email": {"type": "string"},
                "tier": {"type": "string"},
                "open_tickets": {"type": "array"},
                "resolved_tickets": {"type": "array"},
                "total_tickets": {"type": "integer"},
                "avg_sentiment": {"type": "string"},
                "last_contact": {"type": "string"},
            },
        },
    },
    "escalate_to_human": {
        "name": "escalate_to_human",
        "description": "Escalate a conversation to human support",
        "endpoint": "/tools/escalate_to_human",
        "method": "POST",
        "input_schema": {
            "type": "object",
            "properties": {
                "conversation_id": {"type": "string"},
                "customer_id": {"type": "string"},
                "reason": {"type": "string"},
                "tier": {"type": "integer", "enum": [1, 2, 3]},
                "channel": {"type": "string"},
                "current_sentiment": {"type": "string"},
            },
            "required": ["conversation_id", "customer_id", "reason", "tier"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "escalation_id": {"type": "string"},
                "assigned_to": {"type": "string"},
                "expected_response_time": {"type": "string"},
                "ticket_id": {"type": "string"},
                "message": {"type": "string"},
            },
        },
    },
    "send_response": {
        "name": "send_response",
        "description": "Send a formatted response to customer on specified channel",
        "endpoint": "/tools/send_response",
        "method": "POST",
        "input_schema": {
            "type": "object",
            "properties": {
                "conversation_id": {"type": "string"},
                "customer_id": {"type": "string"},
                "channel": {"type": "string"},
                "response_text": {"type": "string"},
                "metadata": {"type": "object"},
            },
            "required": ["conversation_id", "customer_id", "channel", "response_text"],
        },
        "output_schema": {
            "type": "object",
            "properties": {
                "success": {"type": "boolean"},
                "message_id": {"type": "string"},
                "channel": {"type": "string"},
                "sent_at": {"type": "string"},
                "delivery_status": {"type": "string"},
            },
        },
    },
}


# ============================================================================
# FASTAPI APP
# ============================================================================

app = FastAPI(title="NovaDeskAI MCP Server")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# HEALTH CHECK
# ============================================================================

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "NovaDeskAI MCP Server",
        "timestamp": datetime.utcnow().isoformat(),
    }


# ============================================================================
# TOOLS ENDPOINT
# ============================================================================

@app.get("/tools")
async def list_tools():
    """List all available tools with schemas"""
    return {
        "tools": list(TOOLS_REGISTRY.values()),
        "total": len(TOOLS_REGISTRY),
    }


# ============================================================================
# TOOL ENDPOINTS
# ============================================================================

@app.post("/tools/search_knowledge_base")
async def search_knowledge_base(request: SearchKnowledgeBaseRequest):
    """Search product knowledge base"""
    results = kb.search(request.query, request.top_k)
    
    return SearchKnowledgeBaseResponse(
        results=results,
        total_found=len(results),
        query=request.query,
    )


@app.post("/tools/create_ticket")
async def create_ticket(request: CreateTicketRequest):
    """Create a support ticket"""
    ticket_id = f"TKT-{str(uuid.uuid4())[:8].upper()}"
    
    ticket = {
        "ticket_id": ticket_id,
        "customer_id": request.customer_id,
        "customer_name": request.customer_name,
        "email": request.email,
        "channel": request.channel,
        "subject": request.subject,
        "message": request.message,
        "priority": request.priority,
        "tags": request.tags,
        "status": "open",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    
    tickets_db[ticket_id] = ticket
    
    return CreateTicketResponse(
        ticket_id=ticket_id,
        status="open",
        created_at=ticket["created_at"],
        priority=request.priority,
        message=f"Ticket {ticket_id} created successfully",
    )


@app.post("/tools/get_customer_history")
async def get_customer_history(request: CustomerHistoryRequest):
    """Retrieve customer history"""
    customer = None
    
    # Look up by customer_id
    if request.customer_id:
        customer = customers_db.get(request.customer_id)
    # Look up by email
    elif request.email:
        for cust in customers_db.values():
            if cust["email"].lower() == request.email.lower():
                customer = cust
                break
    
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Find customer's tickets
    open_tickets = []
    resolved_tickets = []
    
    for ticket in tickets_db.values():
        if ticket["customer_id"] == customer["customer_id"]:
            ticket_summary = {
                "ticket_id": ticket["ticket_id"],
                "subject": ticket["subject"],
                "status": ticket["status"],
                "priority": ticket["priority"],
                "created_at": ticket["created_at"],
            }
            
            if ticket["status"] == "open":
                open_tickets.append(ticket_summary)
            else:
                resolved_tickets.append(ticket_summary)
    
    # Calculate average sentiment (mock)
    avg_sentiment = "neutral"
    
    return CustomerHistoryResponse(
        customer_id=customer["customer_id"],
        customer_name=customer["customer_name"],
        email=customer["email"],
        tier=customer.get("tier", "standard"),
        open_tickets=open_tickets,
        resolved_tickets=resolved_tickets,
        total_tickets=len(open_tickets) + len(resolved_tickets),
        avg_sentiment=avg_sentiment,
        last_contact=customer.get("last_contact"),
    )


@app.post("/tools/escalate_to_human")
async def escalate_to_human(request: EscalateRequest):
    """Escalate conversation to human support"""
    # Determine agent assignment based on tier
    tier_assignments = {
        1: "bot",
        2: "agent@novadesk.ai",
        3: "senior@novadesk.ai",
    }
    
    response_times = {
        1: "2 hours",
        2: "30 minutes",
        3: "15 minutes",
    }
    
    assigned_to = tier_assignments.get(request.tier, "agent@novadesk.ai")
    expected_time = response_times.get(request.tier, "1 hour")
    
    # Create escalation record
    escalation_id = f"ESC-{str(uuid.uuid4())[:8].upper()}"
    
    # Create associated ticket
    ticket_id = f"TKT-{str(uuid.uuid4())[:8].upper()}"
    
    escalation = {
        "escalation_id": escalation_id,
        "conversation_id": request.conversation_id,
        "customer_id": request.customer_id,
        "reason": request.reason,
        "tier": request.tier,
        "channel": request.channel,
        "sentiment": request.current_sentiment,
        "assigned_to": assigned_to,
        "ticket_id": ticket_id,
        "status": "assigned",
        "created_at": datetime.utcnow().isoformat(),
    }
    
    escalations_db[escalation_id] = escalation
    
    return EscalateResponse(
        escalation_id=escalation_id,
        assigned_to=assigned_to,
        expected_response_time=expected_time,
        ticket_id=ticket_id,
        message=f"Escalation {escalation_id} created and assigned to {assigned_to}",
    )


@app.post("/tools/send_response")
async def send_response(request: SendResponseRequest):
    """Send formatted response on channel"""
    message_id = f"MSG-{str(uuid.uuid4())[:8].upper()}"
    
    message_record = {
        "message_id": message_id,
        "conversation_id": request.conversation_id,
        "customer_id": request.customer_id,
        "channel": request.channel,
        "response_text": request.response_text,
        "metadata": request.metadata,
        "sent_at": datetime.utcnow().isoformat(),
        "delivery_status": "delivered",  # Simulated
    }
    
    sent_messages_db[message_id] = message_record
    
    return SendResponseResponse(
        success=True,
        message_id=message_id,
        channel=request.channel,
        sent_at=message_record["sent_at"],
        delivery_status="delivered",
    )


# ============================================================================
# STARTUP EVENT
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Run on app startup"""
    print("NovaDeskAI MCP Server starting up...")
    print(f"Loaded {len(kb.chunks)} knowledge base chunks")
    print(f"Registered {len(TOOLS_REGISTRY)} tools")


# ============================================================================
# MAIN
# ============================================================================

if __name__ == "__main__":
    uvicorn.run(
        "mcp_server:app",
        host="0.0.0.0",
        port=8001,
        reload=True,
    )

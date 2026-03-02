"""
NovaDeskAI Production API
FastAPI backend for all channels + agent orchestration.
"""
import asyncio, logging, os, sys, uuid
# Ensure project root is in path so 'production' package is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Optional
import uvicorn
from fastapi import FastAPI, HTTPException, Request, Header, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ==================== Pydantic Models ====================

class ProcessMessageRequest(BaseModel):
    message: str
    channel: str
    customer_id: str
    conversation_id: Optional[str] = None


class ProcessMessageResponse(BaseModel):
    response: str
    formatted_response: str
    conversation_id: str
    channel: str
    sentiment: str
    escalated: bool
    tool_calls_made: list
    latency_ms: float


class TicketCreateRequest(BaseModel):
    name: str
    email: EmailStr
    subject: str
    channel: str
    description: str


class TicketResponse(BaseModel):
    ticket_id: str
    status: str
    message: str
    estimated_response_time: str
    created_at: str


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
    services: dict


class StatsResponse(BaseModel):
    total_tickets: int
    by_status: dict
    by_channel: dict
    conversations_active: int


# ==================== In-Memory Storage ====================

tickets_db = {}
conversations_db = {}
metrics_collector = {
    "total_messages_processed": 0,
    "total_agent_calls": 0,
    "total_escalations": 0,
    "by_channel": {},
    "by_sentiment": {},
}


# ==================== Lifespan Management ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("🚀 NovaDeskAI Production API Starting...")
    
    try:
        logger.info("📦 Importing CustomerSuccessAgent...")
        from production.agent.customer_success_agent import CustomerSuccessAgent
        logger.info("✅ CustomerSuccessAgent imported successfully")
        app.state.agent = CustomerSuccessAgent()
    except ImportError as e:
        logger.warning(f"⚠️  Agent not available: {e}")
        app.state.agent = None
    
    try:
        logger.info("📨 Importing channel handlers...")
        from production.channels import gmail_handler, whatsapp_handler, web_form_handler
        logger.info("✅ Channel handlers imported successfully")
    except ImportError as e:
        logger.warning(f"⚠️  Channel handlers not available: {e}")
    
    # Pre-seed sample tickets
    sample_tickets = [
        {
            "ticket_id": "TKT-0001",
            "name": "John Doe",
            "email": "john@example.com",
            "subject": "Integration assistance needed",
            "channel": "email",
            "description": "Need help integrating with our system",
            "status": "open",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "ticket_id": "TKT-0002",
            "name": "Jane Smith",
            "email": "jane@example.com",
            "subject": "WhatsApp setup",
            "channel": "whatsapp",
            "description": "How to configure WhatsApp for my business",
            "status": "in_progress",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
        {
            "ticket_id": "TKT-0003",
            "name": "Bob Johnson",
            "email": "bob@example.com",
            "subject": "API documentation",
            "channel": "gmail",
            "description": "Looking for API documentation",
            "status": "resolved",
            "created_at": datetime.now(timezone.utc).isoformat(),
        },
    ]
    
    for ticket in sample_tickets:
        tickets_db[ticket["ticket_id"]] = ticket
    
    logger.info("✅ Pre-seeded 3 sample tickets")
    logger.info("🎯 NovaDeskAI Production API Ready!")
    
    yield
    
    # Shutdown
    logger.info("🛑 NovaDeskAI Production API Shutting Down...")
    logger.info("📊 Final metrics:")
    logger.info(f"   Total messages processed: {metrics_collector['total_messages_processed']}")
    logger.info(f"   Total escalations: {metrics_collector['total_escalations']}")
    logger.info("✅ Shutdown complete")


# ==================== FastAPI App Setup ====================

app = FastAPI(
    title="NovaDeskAI Customer Success Agent",
    version="2.0.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== Exception Handlers ====================

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        },
    )


# ==================== Health Check ====================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    services_status = {
        "groq": _check_groq_health(),
        "kafka": _check_kafka_health(),
        "database": _check_database_health(),
    }
    
    return HealthResponse(
        status="healthy",
        version="2.0.0",
        timestamp=datetime.now(timezone.utc).isoformat(),
        services=services_status,
    )


def _check_groq_health() -> bool:
    """Check if GROQ API key is configured"""
    return bool(os.getenv("GROQ_API_KEY"))


def _check_kafka_health() -> bool:
    """Check if Kafka is available"""
    return bool(os.getenv("KAFKA_BOOTSTRAP_SERVERS"))


def _check_database_health() -> bool:
    """Check if database is available"""
    return bool(os.getenv("DATABASE_URL"))


# ==================== Message Processing ====================

@app.post("/api/messages/process", response_model=ProcessMessageResponse)
async def process_message(request: ProcessMessageRequest, background_tasks: BackgroundTasks):
    """Process a message through the customer success agent"""
    start_time = datetime.now(timezone.utc)
    
    conversation_id = request.conversation_id or str(uuid.uuid4())
    
    # Initialize conversation if new
    if conversation_id not in conversations_db:
        conversations_db[conversation_id] = {
            "conversation_id": conversation_id,
            "customer_id": request.customer_id,
            "channel": request.channel,
            "messages": [],
            "created_at": start_time.isoformat(),
        }
    
    # Try to use agent if available
    if hasattr(app.state, "agent") and app.state.agent:
        try:
            logger.info(f"Processing message via agent for {request.customer_id}")
            result = await app.state.agent.run(
                request.message,
                request.channel,
                request.customer_id,
                conversation_id,
            )
            
            response_text = result.get("formatted_response") or result.get("response", "")
            sentiment = result.get("sentiment", "neutral")
            escalated = result.get("escalated", False)
            tool_calls = result.get("tool_calls_made", result.get("tool_calls", []))
        except Exception as e:
            logger.error(f"Agent error: {e}")
            response_text = f"Error processing request: {str(e)}"
            sentiment = "neutral"
            escalated = True
            tool_calls = []
    else:
        # Mock response when agent not available
        logger.info("Agent not available, returning mock response")
        response_text = f"[Mock Response] Thank you for your message: '{request.message[:50]}...'"
        sentiment = "positive"
        escalated = False
        tool_calls = []
    
    # Calculate latency
    latency_ms = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
    
    # Add message to conversation
    conversations_db[conversation_id]["messages"].append({
        "timestamp": start_time.isoformat(),
        "role": "user",
        "content": request.message,
    })
    conversations_db[conversation_id]["messages"].append({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "role": "assistant",
        "content": response_text,
        "sentiment": sentiment,
        "escalated": escalated,
    })
    
    # Update metrics
    metrics_collector["total_messages_processed"] += 1
    metrics_collector["by_channel"][request.channel] = metrics_collector["by_channel"].get(request.channel, 0) + 1
    metrics_collector["by_sentiment"][sentiment] = metrics_collector["by_sentiment"].get(sentiment, 0) + 1
    if escalated:
        metrics_collector["total_escalations"] += 1
    
    return ProcessMessageResponse(
        response=response_text,
        formatted_response=response_text,
        conversation_id=conversation_id,
        channel=request.channel,
        sentiment=sentiment,
        escalated=escalated,
        tool_calls_made=tool_calls,
        latency_ms=latency_ms,
    )


# ==================== Conversation Management ====================

@app.get("/api/conversations/{conversation_id}")
async def get_conversation(conversation_id: str):
    """Get conversation context and history"""
    if conversation_id not in conversations_db:
        raise HTTPException(status_code=404, detail="Conversation not found")
    
    return conversations_db[conversation_id]


# ==================== Ticket Management ====================

def _get_estimated_response_time(channel: str) -> str:
    """Get estimated response time based on channel"""
    response_times = {
        "email": "4-24 hours",
        "whatsapp": "1-2 hours",
        "gmail": "2-4 hours",
        "web": "1-2 hours",
    }
    return response_times.get(channel, "2-4 hours")


@app.post("/api/tickets", response_model=TicketResponse)
async def create_ticket(request: TicketCreateRequest):
    """Create a support ticket from web form"""
    ticket_id = f"TKT-{len(tickets_db) + 1:04d}"
    
    ticket = {
        "ticket_id": ticket_id,
        "name": request.name,
        "email": request.email,
        "subject": request.subject,
        "channel": request.channel,
        "description": request.description,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    tickets_db[ticket_id] = ticket
    logger.info(f"Created ticket {ticket_id} from {request.email}")
    
    return TicketResponse(
        ticket_id=ticket_id,
        status="open",
        message="Ticket created successfully",
        estimated_response_time=_get_estimated_response_time(request.channel),
        created_at=ticket["created_at"],
    )


@app.get("/api/tickets")
async def list_tickets(status: Optional[str] = None):
    """List all tickets, optionally filtered by status"""
    tickets = list(tickets_db.values())
    
    if status:
        tickets = [t for t in tickets if t["status"] == status]
    
    return {
        "total": len(tickets),
        "tickets": tickets,
    }


@app.get("/api/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Get a single ticket by ID"""
    if ticket_id not in tickets_db:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    return tickets_db[ticket_id]


@app.put("/api/tickets/{ticket_id}/status")
async def update_ticket_status(ticket_id: str, body: dict):
    """Update ticket status"""
    if ticket_id not in tickets_db:
        raise HTTPException(status_code=404, detail="Ticket not found")
    
    if "status" not in body:
        raise HTTPException(status_code=400, detail="status field required")
    
    tickets_db[ticket_id]["status"] = body["status"]
    logger.info(f"Updated ticket {ticket_id} status to {body['status']}")
    
    return {
        "ticket_id": ticket_id,
        "status": body["status"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }


# ==================== Dashboard Stats ====================

@app.get("/api/stats", response_model=StatsResponse)
async def get_stats():
    """Get dashboard statistics"""
    by_status = {}
    by_channel = {}
    
    for ticket in tickets_db.values():
        status = ticket["status"]
        channel = ticket["channel"]
        
        by_status[status] = by_status.get(status, 0) + 1
        by_channel[channel] = by_channel.get(channel, 0) + 1
    
    return StatsResponse(
        total_tickets=len(tickets_db),
        by_status=by_status,
        by_channel=by_channel,
        conversations_active=len(conversations_db),
    )


# ==================== Metrics ====================

@app.get("/api/metrics")
async def get_metrics():
    """Get metrics summary"""
    return {
        "total_messages_processed": metrics_collector["total_messages_processed"],
        "total_agent_calls": metrics_collector["total_agent_calls"],
        "total_escalations": metrics_collector["total_escalations"],
        "by_channel": metrics_collector["by_channel"],
        "by_sentiment": metrics_collector["by_sentiment"],
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ==================== Webhooks ====================

@app.get("/webhook/whatsapp")
async def whatsapp_webhook_verify(request: Request):
    """WhatsApp webhook verification — works without handler import"""
    params = request.query_params
    hub_mode = params.get("hub.mode")
    hub_verify_token = params.get("hub.verify_token")
    hub_challenge = params.get("hub.challenge")
    verify_token = os.getenv("WHATSAPP_VERIFY_TOKEN", "novadesk_verify")
    if hub_mode == "subscribe" and hub_verify_token == verify_token:
        logger.info("WhatsApp webhook verified successfully")
        return int(hub_challenge) if hub_challenge and hub_challenge.isdigit() else hub_challenge
    logger.warning(f"WhatsApp verify failed: mode={hub_mode}, token={hub_verify_token}")
    raise HTTPException(status_code=403, detail="Invalid verification token")


@app.post("/webhook/whatsapp")
async def whatsapp_webhook_receive(
    request: Request,
    x_hub_signature_256: Optional[str] = Header(None),
):
    """WhatsApp incoming messages webhook"""
    import json
    body = await request.body()
    payload = json.loads(body)
    messages_processed = 0

    try:
        from production.channels.whatsapp_handler import WhatsAppHandler
        handler = WhatsAppHandler()

        # Validate signature only if provided (skip in dev/test)
        if x_hub_signature_256:
            if not handler.validate_signature(body, x_hub_signature_256):
                raise HTTPException(status_code=403, detail="Invalid signature")

        # Extract messages — pass full payload directly to process_webhook
        normalized_messages = await handler.process_webhook(payload)

        # Count all parsed messages (even if agent is unavailable)
        messages_processed = len(normalized_messages)

        # Process each message through agent
        for msg in normalized_messages:
            if hasattr(app.state, "agent") and app.state.agent:
                try:
                    customer_id = f"wa_{msg.get('customer_phone', 'unknown').replace('+', '')}"
                    result = await app.state.agent.run(
                        msg.get("content", ""),
                        "whatsapp",
                        customer_id,
                        None,
                    )
                    # Send reply back via WhatsApp
                    reply = result.get("formatted_response") or result.get("response", "")
                    if reply and msg.get("customer_phone"):
                        await handler.send_text_message(msg["customer_phone"], reply)
                    logger.info(f"WhatsApp message processed for {customer_id}, escalated={result.get('escalated')}")
                except Exception as e:
                    logger.error(f"Error processing WhatsApp message: {e}", exc_info=True)

        return {"status": "ok", "processed": messages_processed}

    except ImportError:
        logger.warning("WhatsApp handler not available — processing directly")
        # Fallback: extract messages directly from payload
        if "entry" in payload:
            for entry in payload["entry"]:
                for change in entry.get("changes", []):
                    value = change.get("value", {})
                    for msg in value.get("messages", []):
                        text = msg.get("text", {}).get("body", "")
                        phone = msg.get("from", "")
                        if text and hasattr(app.state, "agent") and app.state.agent:
                            try:
                                await app.state.agent.run(text, "whatsapp", f"wa_{phone}", None)
                                messages_processed += 1
                            except Exception as e:
                                logger.error(f"Fallback WhatsApp error: {e}")
        return {"status": "ok", "processed": messages_processed}


@app.post("/webhook/gmail")
async def gmail_webhook_receive(request: Request):
    """Gmail Pub/Sub webhook for incoming emails"""
    try:
        from production.channels.gmail_handler import handle_gmail_webhook
        
        body = await request.json()
        
        messages_processed = 0
        
        # Process Pub/Sub push notification
        # Body can be the full Pub/Sub envelope OR just the message dict
        pubsub_body = body.get("message", body)
        
        normalized_list = await handle_gmail_webhook(pubsub_body)
        messages_processed = len(normalized_list)
        
        # Process each normalized message through agent and auto-reply
        for normalized in normalized_list:
            if hasattr(app.state, "agent") and app.state.agent:
                try:
                    customer_email = normalized.get("customer_email", "")
                    customer_id = f"email_{customer_email.replace('@','_').replace('.','_')}"
                    result = await app.state.agent.run(
                        normalized.get("content", ""),
                        "email",
                        customer_id,
                        None,
                    )
                    logger.info(f"Gmail message processed for {customer_id}, escalated={result.get('escalated')}")

                    # ✅ Auto-reply back to customer via Gmail
                    reply = result.get("formatted_response") or result.get("response", "")
                    if reply and customer_email:
                        try:
                            from production.channels.gmail_handler import GmailHandler
                            gmail = GmailHandler()
                            if gmail.available:
                                await gmail.send_reply(
                                    to_email=customer_email,
                                    subject=normalized.get("subject", "Re: Your Support Request"),
                                    body=reply,
                                    thread_id=normalized.get("thread_id"),
                                )
                                logger.info(f"✅ Auto-replied to {customer_email} via Gmail")
                            else:
                                logger.warning(f"Gmail handler not available for auto-reply to {customer_email}")
                        except Exception as e:
                            logger.error(f"Failed to send Gmail auto-reply to {customer_email}: {e}")
                except Exception as e:
                    logger.error(f"Error processing Gmail message: {e}")
        
        return {"status": "ok", "processed": messages_processed}
    
    except ImportError:
        logger.warning("Gmail handler not available")
        return {"status": "ok", "processed": 0}


# ==================== Web Form Handler Router ====================

try:
    from production.channels.web_form_handler import router as web_form_router
    app.include_router(web_form_router)
except ImportError:
    logger.warning("Web form handler not available")


# ==================== Root & Support ====================

@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "NovaDeskAI Customer Success Agent",
        "version": "2.0.0",
        "status": "running",
        "docs": "/docs",
        "health": "/health",
    }


@app.post("/support/submit")
async def submit_support_form(request: TicketCreateRequest):
    """Web form submission endpoint"""
    ticket_id = f"TKT-{len(tickets_db) + 1:04d}"
    
    ticket = {
        "ticket_id": ticket_id,
        "name": request.name,
        "email": request.email,
        "subject": request.subject,
        "channel": request.channel,
        "description": request.description,
        "status": "open",
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    
    tickets_db[ticket_id] = ticket
    logger.info(f"Created support ticket {ticket_id} from {request.email}")
    
    return {
        "ticket_id": ticket_id,
        "status": "open",
        "message": "Your support request has been received",
        "estimated_response_time": _get_estimated_response_time(request.channel),
        "created_at": ticket["created_at"],
    }


# ==================== Main ====================

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=False)

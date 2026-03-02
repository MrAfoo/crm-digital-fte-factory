# NovaDeskAI Customer Success Agent

**AI-Powered Customer Support Platform**

NovaDeskAI is an intelligent customer success agent that automates support ticket management, processes customer messages, and provides AI-driven responses. It combines a modern web form interface with a powerful FastAPI backend to deliver seamless customer support workflows.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                                                               │
│  Customer Browser / iframe Embedding                         │
│  ┌─────────────────────────────────────────────────────┐   │
│  │        NovaDeskAI Web Form (index.html)             │   │
│  │  • Real-time validation                             │   │
│  │  • Support ticket submission                        │   │
│  │  • Character counters, loading states               │   │
│  └──────────────────────┬────────────────────────────┘   │
│                         │                                  │
│                    HTTP/JSON                              │
│                    POST /api/tickets                       │
│                         │                                  │
└─────────────────────────┼──────────────────────────────────┘
                          │
                ┌─────────▼──────────┐
                │   FastAPI Server   │
                │  (localhost:8000)  │
                └─────────────────────┘
                          │
        ┌─────────────────┼─────────────────┐
        │                 │                 │
    ┌───▼────────┐  ┌────▼─────┐  ┌───────▼────┐
    │  Tickets   │  │Conversations │ Agent Loop│
    │   (In-Mem) │  │  (In-Mem)    │ (Optional) │
    └────────────┘  └──────────────┘ └────────────┘
        │
    API Endpoints:
    • POST   /api/tickets
    • GET    /api/tickets
    • GET    /api/tickets/{id}
    • PUT    /api/tickets/{id}/status
    • POST   /api/messages/process
    • GET    /api/conversations/{id}
    • GET    /api/health
    • GET    /api/stats
```

---

## Quick Start

### Prerequisites

- Python 3.8+
- pip (Python package manager)

### Installation

1. **Clone/Navigate to the project:**
   ```bash
   cd novadeskai
   ```

2. **Install dependencies:**
   ```bash
   pip install fastapi uvicorn pydantic email-validator
   ```

3. **Start the API server:**
   ```bash
   python src/api/main.py
   ```
   The API will be available at `http://localhost:8000`

4. **Open the web form:**
   - Standalone: Open `src/web-form/index.html` directly in your browser
   - Or via local server: `http://localhost:8000/web-form/` (if serving static files)

### First Steps

- Visit the web form and submit a test ticket
- Check the API stats: `http://localhost:8000/api/stats`
- View all tickets: `http://localhost:8000/api/tickets`
- Check API health: `http://localhost:8000/api/health`

---

## Project Structure

```
novadeskai/
├── src/
│   ├── api/
│   │   ├── __init__.py
│   │   └── main.py              # FastAPI application & endpoints
│   ├── agent/
│   │   ├── __init__.py
│   │   └── prototype.py          # (Optional) AI agent logic
│   └── web-form/
│       ├── index.html            # Self-contained support form
│       └── README.md             # Form documentation
├── README.md                      # This file
└── requirements.txt               # Python dependencies (optional)
```

---

## API Reference

### Authentication
No authentication required (CORS enabled for all origins).

### Base URL
```
http://localhost:8000
```

### Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/tickets` | Create a new support ticket |
| `GET` | `/api/tickets` | List all tickets (with optional status filter) |
| `GET` | `/api/tickets/{ticket_id}` | Get ticket details |
| `PUT` | `/api/tickets/{ticket_id}/status` | Update ticket status |
| `POST` | `/api/messages/process` | Process message through AI agent |
| `GET` | `/api/conversations/{conversation_id}` | Get conversation state |
| `GET` | `/api/health` | Health check |
| `GET` | `/api/stats` | Dashboard statistics |

#### 1. Create Ticket
```http
POST /api/tickets
Content-Type: application/json

{
  "name": "John Doe",
  "email": "john@example.com",
  "subject": "Billing issue",
  "channel": "Web",
  "description": "I was charged twice for my subscription this month. Please help me resolve this issue."
}
```

**Response (200 OK):**
```json
{
  "ticket_id": "TKT-7432",
  "status": "open",
  "message": "Your support ticket has been created successfully.",
  "estimated_response_time": "< 2 minutes",
  "created_at": "2024-01-15T10:30:00.000000"
}
```

#### 2. List Tickets
```http
GET /api/tickets?status=open
```

**Response (200 OK):**
```json
{
  "tickets": [
    {
      "ticket_id": "TKT-7432",
      "name": "John Doe",
      "email": "john@example.com",
      "subject": "Billing issue",
      "channel": "Web",
      "description": "...",
      "status": "open",
      "priority": "high",
      "created_at": "2024-01-15T10:30:00.000000",
      "updated_at": "2024-01-15T10:30:00.000000"
    }
  ],
  "total": 1
}
```

#### 3. Get Ticket Details
```http
GET /api/tickets/TKT-7432
```

**Response (200 OK):**
```json
{
  "ticket_id": "TKT-7432",
  "name": "John Doe",
  "email": "john@example.com",
  "subject": "Billing issue",
  "channel": "Web",
  "description": "...",
  "status": "open",
  "priority": "high",
  "created_at": "2024-01-15T10:30:00.000000",
  "updated_at": "2024-01-15T10:30:00.000000"
}
```

#### 4. Update Ticket Status
```http
PUT /api/tickets/TKT-7432/status
Content-Type: application/json

{
  "status": "in_progress"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Ticket TKT-7432 status updated to in_progress",
  "ticket": { ... }
}
```

#### 5. Process Message
```http
POST /api/messages/process
Content-Type: application/json

{
  "message": "Can you help me with my billing issue?",
  "channel": "Web",
  "customer_id": "cust_12345",
  "conversation_id": "conv_optional"
}
```

**Response (200 OK):**
```json
{
  "response": "Thank you for contacting NovaDeskAI. A support specialist will assist you shortly.",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "agent_action": "respond",
  "confidence": 0.95,
  "requires_escalation": false
}
```

#### 6. Get Conversation
```http
GET /api/conversations/550e8400-e29b-41d4-a716-446655440000
```

**Response (200 OK):**
```json
{
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "customer_id": "cust_12345",
  "status": "active",
  "messages": [
    {
      "role": "customer",
      "message": "Can you help me?",
      "timestamp": "2024-01-15T10:30:00.000000"
    },
    {
      "role": "agent",
      "message": "Of course! How can I assist?",
      "timestamp": "2024-01-15T10:30:05.000000"
    }
  ],
  "created_at": "2024-01-15T10:30:00.000000",
  "updated_at": "2024-01-15T10:30:05.000000"
}
```

#### 7. Health Check
```http
GET /api/health
```

**Response (200 OK):**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "timestamp": "2024-01-15T10:30:00.000000"
}
```

#### 8. Dashboard Stats
```http
GET /api/stats
```

**Response (200 OK):**
```json
{
  "total_tickets": 5,
  "by_status": {
    "open": 2,
    "in_progress": 2,
    "resolved": 1,
    "escalated": 0
  },
  "by_channel": {
    "Web": 2,
    "Email": 2,
    "WhatsApp": 1
  },
  "by_priority": {
    "low": 1,
    "medium": 1,
    "high": 2,
    "critical": 1
  },
  "avg_response_time": "< 2 minutes"
}
```

---

## Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `GROQ_API_KEY` | Groq LLM API key for agent responses | (none) | Optional |
| `API_HOST` | API server host | `0.0.0.0` | No |
| `API_PORT` | API server port | `8000` | No |
| `LOG_LEVEL` | Logging level (debug, info, warning, error) | `info` | No |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | `*` (all) | No |
| `WHATSAPP_TOKEN` | Meta WhatsApp Cloud API token | (none) | Optional |
| `WHATSAPP_PHONE_NUMBER_ID` | Meta WhatsApp Phone Number ID | (none) | Optional |
| `WHATSAPP_VERIFY_TOKEN` | WhatsApp webhook verification token | `novadesk_verify` | No |

### Setting Environment Variables

**Linux/macOS:**
```bash
export GROQ_API_KEY="your-api-key-here"
python src/api/main.py
```

**Windows (PowerShell):**
```powershell
$env:GROQ_API_KEY = "your-api-key-here"
python src/api/main.py
```

**Windows (Command Prompt):**
```cmd
set GROQ_API_KEY=your-api-key-here
python src/api/main.py
```

---

## Web Form Features

The embeddable customer support form (`src/web-form/index.html`) includes:

- ✅ **Real-time Validation** - Fields validate as you type
- ✅ **Required Fields** - Full Name, Email, Subject, Channel, Description
- ✅ **Character Counter** - Max 1000 characters on description
- ✅ **Channel Options** - Web, Email, WhatsApp
- ✅ **Loading States** - Spinner during submission
- ✅ **Success Confirmation** - Shows ticket number (TKT-XXXX)
- ✅ **Error Handling** - Network error messages with retry
- ✅ **Responsive Design** - Mobile and desktop optimized
- ✅ **Accessibility** - ARIA labels, keyboard navigation
- ✅ **No Dependencies** - Pure HTML/CSS/JS (Google Fonts only)
- ✅ **iframe Ready** - Post-message communication support

> **Note:** This project uses the **Meta WhatsApp Cloud API** (free) instead of Twilio.  
> Twilio charges per message. Meta's Cloud API is free for the first 1,000 conversations/month.  
> See: https://developers.facebook.com/docs/whatsapp/cloud-api

**Embed in your website:**
```html
<iframe 
  src="http://localhost:8000/web-form/" 
  width="600" 
  height="900" 
  frameborder="0">
</iframe>
```

See `src/web-form/README.md` for detailed form documentation.

---

## Development

### Adding a Custom Agent

Create `src/agent/prototype.py` with an `AgentLoop` class:

```python
class AgentLoop:
    def process(self, message: str, channel: str) -> dict:
        """Process a message and return agent response"""
        return {
            "text": "Your agent response here",
            "action": "respond",  # or "escalate", "create_ticket"
            "confidence": 0.95,
            "requires_escalation": False
        }
```

The API will automatically use it when available.

### Running Tests

```bash
# With pytest (install: pip install pytest pytest-asyncio httpx)
pytest tests/
```

### Database Persistence

Currently uses in-memory storage. To persist data:

1. Install SQLAlchemy: `pip install sqlalchemy`
2. Modify `src/api/main.py` to use SQLite, PostgreSQL, etc.
3. Define SQLAlchemy ORM models

---

## Deployment

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY src/ src/

CMD ["python", "src/api/main.py"]
```

```bash
docker build -t novadeskai .
docker run -p 8000:8000 novadeskai
```

### Cloud Platforms

- **Heroku**: Add `Procfile`: `web: python src/api/main.py`
- **AWS Lambda**: Use Mangum: `pip install mangum`
- **Google Cloud Run**: Similar Docker setup
- **Render.com**: Push to Git, auto-deploy

### Environment Variables in Production

Set via platform-specific methods:
- Heroku: `heroku config:set GROQ_API_KEY=...`
- AWS: Secrets Manager
- Docker: `docker run -e GROQ_API_KEY=... ...`

---

## Troubleshooting

### Port 8000 Already in Use
```bash
# Find and kill the process using port 8000
lsof -i :8000
kill -9 <PID>

# Or use a different port
python src/api/main.py --port 8001
```

### CORS Errors
The API has CORS enabled for all origins. If you still see errors:
- Check browser console for detailed error message
- Verify API is running on `http://localhost:8000`
- Ensure Content-Type headers are correct

### Form Won't Submit
- Check browser console for validation errors
- Verify API endpoint is correct in the form
- Check API is running: `curl http://localhost:8000/api/health`

### Agent Not Responding
If the agent seems unresponsive:
- Check `src/agent/prototype.py` exists and is properly formatted
- Verify GROQ_API_KEY is set (if using Groq API)
- Check API logs for errors

---

## License

MIT License - See LICENSE file for details

---

## Support

For issues, feature requests, or questions:

1. Check existing documentation in `src/web-form/README.md`
2. Review API endpoint specifications above
3. Check troubleshooting section
4. Create an issue with detailed reproduction steps

---

## Roadmap

- [ ] Database persistence (PostgreSQL)
- [ ] Authentication & authorization
- [ ] Agent AI integration (Groq/OpenAI)
- [ ] Ticket assignment workflow
- [ ] Email notifications
- [ ] Admin dashboard
- [ ] Analytics & reporting
- [ ] Multi-language support
- [ ] Mobile app
- [ ] Webhook integrations

---

**Built with ❤️ by the NovaDeskAI Team**

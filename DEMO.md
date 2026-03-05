# NovaDeskAI — Live Demo Script
**Hackathon:** CRM Digital FTE Factory Final Hackathon 5
**Project:** Customer Success AI Agent
**Date:** 2026-02-27

## What This System Does (30 seconds elevator pitch)

NovaDeskAI is a production-grade AI Customer Success Agent (Digital FTE) that:
- Handles customer queries 24/7 across Email, WhatsApp, and Web Form
- Uses Groq llama-3.3-70b-versatile for sub-2s AI responses
- Auto-escalates angry/urgent cases to human agents
- Tracks all interactions in a PostgreSQL CRM with full metrics
- Streams events through Kafka for async processing
- Scales on Kubernetes (Kind) with HPA (2-10 replicas)

## Architecture (ASCII diagram)

```
Channels          Webhook Layer         Agent Core          Infrastructure
─────────         ─────────────         ──────────          ──────────────
WhatsApp    →     /webhook/whatsapp  →                  →   PostgreSQL (CRM)
Gmail       →     /webhook/gmail     →   Groq LLM       →   Kafka (Events)
Web Form    →     /support/submit    →   + 5 Tools      →   Kubernetes (Kind)
                                         + Formatters   →   Kafka UI (:8080)
                  FastAPI (:8000)         + Escalation
```

## System Status Check (Open These URLs)

| URL | Expected Result |
|-----|-----------------|
| http://localhost:8000/health | {"status":"healthy","version":"2.0.0","groq":true} |
| http://localhost:8000/api/stats | Total tickets, by channel |
| http://localhost:8000/api/tickets | All tickets list |
| http://localhost:8000/api/metrics | CSAT, response times |
| http://localhost:8001/tools | 5 MCP tools listed |
| http://localhost:8080 | Kafka UI - 5 topics |

## Demo 1: WhatsApp Live Message (2 minutes)

### Setup:
- API running: `python production/api/main.py`  
- ngrok: `https://chloe-dianoetic-hoggishly.ngrok-free.dev → :8000`
- WhatsApp test number: `+1 555 145 8166`

### Steps:
1. Open WhatsApp on phone
2. Send to `+1 555 145 8166`:
   ```
   Hi, I need help with my billing. Can't find my invoice.
   ```
3. Watch ngrok dashboard: http://localhost:4040
4. Expected Nova reply (within 3-5 seconds):
   ```
   Hi! I can help with your invoice. You can find it in Settings → Billing → Invoice History. Need the direct link? 📄
   ```
5. Show the ngrok dashboard — POST /webhook/whatsapp → 200 OK

### What it shows:
- Real-time WhatsApp message processing
- Groq LLM generating channel-appropriate response (<300 chars)
- Sentiment detection (neutral)
- No escalation triggered

## Demo 2: Escalation Trigger (2 minutes)

### Send this angry message on WhatsApp:
```
This is outrageous! I want to speak to a lawyer!
```

### Expected behavior:
- Sentiment: angry (score < 0.3)
- Escalation: YES → Tier 3 (legal keyword detected)
- ESC-XXXX reference number returned
- Human agent notified

### Show in API:
```
http://localhost:8000/api/stats  
→ escalation_count: 1
```

## Demo 3: Gmail Email (2 minutes)

### Send email to: affanali.2006aa@gmail.com
- Subject: `Cannot connect Gmail integration`
- Body: `Hi, I've been trying to set up the Gmail integration but it keeps failing with error 403. I'm on the Growth plan. Please help.`

### What happens:
1. Gmail receives email
2. Pub/Sub pushes notification to `/webhook/gmail`
3. Nova processes with formal email formatting
4. Response sent back via Gmail API
5. Check ngrok: POST /webhook/gmail → 200 OK

## Demo 4: Web Form (1 minute)

1. Open: `web-form-nextjs` in browser
2. Fill in:
   - Name: Judge Demo
   - Email: judge@hackathon.com  
   - Subject: Testing NovaDeskAI
   - Description: This is a test submission from the hackathon judge.
3. Click Submit
4. Shows: TKT-XXXX confirmation
5. Check: http://localhost:8000/api/tickets — new ticket appears!

## Demo 5: Kafka Message Flow (1 minute)

1. Open: http://localhost:8080 (Kafka UI)
2. Click nova-cluster → Topics
3. Show 5 topics: inbound, processed, escalations, tickets, dlq
4. Click nova.messages.inbound → Messages
5. Show actual JSON payloads from the WhatsApp/Gmail messages

## Demo 6: Run Automated Demo (2 minutes)

```powershell
python setup/demo_runner.py
```

Shows 5 scenarios with:
- Sentiment analysis results
- Escalation decisions  
- Channel-formatted responses
- Response times
- Final summary table

## Test Suite (30 seconds)

```powershell
python -m pytest tests/ production/tests/ -q
```
Expected: **222 tests passing in ~2 seconds**

## Key Technical Highlights for Judges

| Feature | Implementation |
|---------|---------------|
| LLM | Groq llama-3.3-70b-versatile (sub-2s) |
| WhatsApp | Meta Cloud API (free, not Twilio) |
| Gmail | Gmail API + Pub/Sub push notifications |
| Database | PostgreSQL + pgvector for semantic search |
| Streaming | Apache Kafka (self-hosted via Docker) |
| Deployment | Kubernetes via Kind + HPA auto-scaling |
| Tests | 222 pytest tests (127 Stage1 + 95 Stage2) |
| Channels | Email, WhatsApp, Web Form |
| Escalation | 3-tier: Bot → Agent → Senior Manager |
| Memory | In-memory (Phase 1) + PostgreSQL schema (Phase 2) |

## Judging Criteria Checklist

- [x] Working prototype handles queries from all 3 channels
- [x] Discovery log documents requirements exploration
- [x] MCP server with 5+ tools
- [x] Agent skills defined and tested
- [x] Edge cases documented (25+ cases)
- [x] Escalation rules crystallized
- [x] Channel-specific templates
- [x] Performance baseline measured
- [x] Production folder structure
- [x] PostgreSQL CRM schema
- [x] Kafka event streaming
- [x] Kubernetes manifests (Kind)
- [x] Docker Compose for local run
- [x] 222 automated tests
- [x] Live webhook integrations

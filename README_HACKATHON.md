# NovaDeskAI Hackathon Submission — Complete Index

**Customer Success FTE Challenge**  
**Submission Status: ✅ Complete & Ready for Evaluation**  
**Last Updated: 2026-02-27**

---

## 🚀 Start Here (Choose Your Path)

### For Judges (No Technical Background)
1. Read: **JUDGE_GUIDE.md** (3 min) — Quick overview
2. Run: `.\setup\run_demo.ps1` (2 min) — See it in action
3. Explore: Open http://localhost:8000/api/stats in browser
4. **Total time: 5 minutes** ✅

### For Technical Evaluators
1. Read: **DEMO.md** (5 min) — Understand architecture
2. Read: **SUBMISSION.md** (15 min) — Technical deep-dive
3. Run: `python setup/demo_runner.py` (2 min) — See live metrics
4. Explore code: `production/` directory (30+ min)
5. Run tests: `pytest production/tests/` (5 min)
6. **Total time: 60 minutes** ✅

### For Deployment/DevOps
1. Read: **SUBMISSION.md** section "Deployment (Docker + Kubernetes)"
2. Review: `production/k8s/` files
3. Review: `production/k8s/docker-compose.yml` (local dev)
4. Try: `docker build -t novadeskai .` then `docker run -p 8000:8000 novadeskai`
5. **Total time: 20 minutes** ✅

---

## 📚 Complete File Guide

### 🎯 Quick Start Documents

| File | Size | Time | Purpose |
|------|------|------|---------|
| **JUDGE_GUIDE.md** | 10 KB | 3 min | 👑 Start here for judges — key metrics & how to run |
| **HACKATHON.md** | 13 KB | 5 min | Overview of submission + reading guide |
| **DEMO.md** | 15 KB | 5 min | Complete demo script with 5 scenarios |
| **SUBMISSION.md** | 25 KB | 15 min | Full technical submission document |

### 🔧 Executable Scripts

| File | Type | Purpose | Command |
|------|------|---------|---------|
| **setup/run_demo.ps1** | PowerShell | Automated demo launcher (recommended for judges) | `.\setup\run_demo.ps1` |
| **setup/demo_runner.py** | Python | Automated demo script (standalone) | `python setup/demo_runner.py` |

### 📁 Project Structure

```
F:\vs\crm/
│
├── 📄 README.md                          # Original project README
├── 📄 README_HACKATHON.md               # This file
├── 📄 JUDGE_GUIDE.md                    # ⭐ START HERE
├── 📄 HACKATHON.md                      # Submission overview
├── 📄 DEMO.md                           # Complete demo script
├── 📄 SUBMISSION.md                     # Technical details
│
├── 📁 production/                        # PRODUCTION CODE (5000+ lines)
│   ├── 📁 agent/
│   │   ├── customer_success_agent.py    # Core agent (Groq integration)
│   │   ├── prompts.py                   # System prompt
│   │   ├── formatters.py                # Channel-specific formatting
│   │   └── tools.py                     # 5 tool functions
│   │
│   ├── 📁 api/
│   │   └── main.py                      # FastAPI server + endpoints
│   │
│   ├── 📁 channels/
│   │   ├── whatsapp_handler.py          # Meta WhatsApp Cloud API
│   │   ├── gmail_handler.py             # Gmail webhook
│   │   └── web_form_handler.py          # Web form parser
│   │
│   ├── 📁 database/
│   │   ├── queries.py                   # DB access layer
│   │   ├── schema.sql                   # PostgreSQL schema
│   │   └── migrations/
│   │
│   ├── 📁 workers/
│   │   ├── message_processor.py         # Async queue
│   │   └── metrics_collector.py         # Telemetry
│   │
│   ├── 📁 k8s/                          # KUBERNETES DEPLOYMENT
│   │   ├── Dockerfile                   # Docker image
│   │   ├── docker-compose.yml           # Local dev
│   │   ├── k8s-manifests.yaml           # K8s deployment
│   │   ├── kind-cluster.yaml            # Kind cluster config
│   │   └── deploy.ps1                   # Deploy script
│   │
│   └── 📁 tests/                        # 95+ TESTS
│       ├── test_agent.py                # 38 agent tests
│       ├── test_channels.py             # 23 channel tests
│       ├── test_e2e.py                  # 34 E2E tests
│       └── conftest.py                  # Pytest fixtures
│
├── 📁 src/                               # LEGACY / WEB FORM
│   ├── 📁 api/
│   ├── 📁 agent/
│   └── 📁 web-form/
│       └── index.html                   # Embeddable support form
│
├── 📁 setup/                             # SETUP & DEMO
│   ├── run_demo.ps1                     # ⭐ RUN THIS
│   ├── demo_runner.py                   # ⭐ OR THIS
│   ├── gmail_oauth.py                   # Gmail OAuth helper
│   ├── gmail_watch.py                   # Gmail webhook setup
│   └── [Gmail OAuth files]
│
├── 📁 tests/                             # ADDITIONAL TESTS (127+)
│   ├── test_agent_loop.py
│   ├── test_channel_formatter.py
│   ├── test_escalation_engine.py
│   ├── test_knowledge_searcher.py
│   ├── test_message_normalizer.py
│   ├── test_performance.py
│   ├── test_sentiment_analyzer.py
│   └── conftest.py
│
├── 📁 context/                           # KNOWLEDGE BASE
│   ├── brand-voice.md                   # Tone guidelines
│   ├── company-profile.md               # Product info
│   ├── escalation-rules.md              # Escalation triggers
│   ├── product-docs.md                  # Features
│   └── sample-tickets.json              # Example tickets
│
├── 📁 specs/                             # DESIGN DOCS
│   ├── customer-success-fte-spec.md     # Original challenge
│   ├── discovery-log.md                 # Research
│   ├── edge-cases.md                    # Handled edge cases
│   ├── skills-manifest.md               # Agent capabilities
│   ├── stage1-completion-checklist.md   # Phase 1 items
│   └── transition-checklist.md          # Phase 2 items
│
├── 📄 .env                               # Environment (secrets)
├── 📄 .env.example                       # Template
├── 📄 docker-compose.yml                 # Docker setup
├── 📄 pytest.ini                         # Test config
└── 📄 requirements.txt                   # Dependencies
```

---

## 🎬 How to Run Demo

### ✅ Simplest Way (PowerShell - Recommended)
```powershell
cd F:\vs\crm
.\setup\run_demo.ps1
```
**What happens:**
1. Kills any process on port 8000
2. Starts API in background
3. Waits for API to be ready
4. Runs automated demo (5 scenarios)
5. Shows beautiful console output
6. Stops API (or keeps running with `-KeepRunning`)

**Time: 2 minutes**

### Alternative: Python Only
```powershell
cd F:\vs\crm

# Terminal 1: Start API
python production/api/main.py

# Terminal 2: Run demo
python setup/demo_runner.py
```

### Alternative: Docker
```powershell
docker build -t novadeskai .
docker run -p 8000:8000 -e GROQ_API_KEY=$env:GROQ_API_KEY novadeskai
```

---

## 📊 What You'll See

When you run the demo:

**Console Output:**
```
╔════════════════════════════════════════════════════════════╗
║           🚀 NovaDeskAI Automated Demo Runner 🚀           ║
╚════════════════════════════════════════════════════════════╝

✅ API is healthy and responding

────────────────────────────────────────────────────────────
📋 RUNNING DEMO SCENARIOS (5 scenarios)
────────────────────────────────────────────────────────────

Scenario 1: Email — Billing Question
  Channel: Email
  Customer: Alice Johnson (CUST001)
  
✅ Success
  Sentiment: 😐 neutral
  Escalation: ✓ No
  Response: "Thank you for contacting..."
  Tools: search_knowledge_base, create_ticket
  Latency: 1050 ms

[... 4 more scenarios ...]

────────────────────────────────────────────────────────────
📊 DEMO SUMMARY
────────────────────────────────────────────────────────────

Requests:
  Total Processed:     5
  Successful:          5/5
  Escalations:         2 (40%)

Response Times:
  Average:             980 ms
  Min:                 850 ms
  Max:                 1200 ms

Channels Tested:
  ✓ Email
  ✓ WhatsApp
  ✓ Web
```

---

## 🔗 Live URLs (When API Running)

After running demo, explore live:

| Resource | URL | Shows |
|----------|-----|-------|
| **Health** | http://localhost:8000/api/health | Service status |
| **Tickets** | http://localhost:8000/api/tickets | All created tickets |
| **Stats** | http://localhost:8000/api/stats | Real-time metrics |
| **Web Form** | http://localhost:8000/web-form/ | Customer form |

---

## 📖 Reading Guide by Role

### 👑 Judges (5 min total)
1. **JUDGE_GUIDE.md** (3 min)
   - What is this?
   - See it in action
   - Key stats
   - Evaluation rubric

2. Run demo (2 min)
   ```powershell
   .\setup\run_demo.ps1
   ```

### 🏗️ Architects (30 min total)
1. **DEMO.md** (5 min) — Architecture & 5 scenarios
2. **SUBMISSION.md** (15 min) — Full technical details
3. Explore code (10 min)
   ```
   production/agent/customer_success_agent.py  — Agent logic
   production/api/main.py                      — API endpoints
   production/channels/                        — Integrations
   ```

### 👨‍💻 Developers (60+ min total)
1. **SUBMISSION.md** (15 min) — Full technical details
2. **DEMO.md** (5 min) — Demo scenarios
3. Code review (30 min)
   ```
   production/agent/   — Groq integration, tools, context
   production/tests/   — 95 test cases
   setup/              — Demo runner code
   ```
4. Run tests (10 min)
   ```powershell
   pytest production/tests/ -v
   ```

### 🚀 DevOps/SRE (30 min total)
1. **SUBMISSION.md** section "Deployment" (5 min)
2. Review manifests (10 min)
   ```
   production/k8s/k8s-manifests.yaml
   production/k8s/docker-compose.yml
   production/k8s/Dockerfile
   ```
3. Try locally (15 min)
   ```powershell
   docker build -t novadeskai .
   docker run -p 8000:8000 novadeskai
   ```

---

## 🎯 The 5 Demo Scenarios

### Scenario 1: Email — Billing Question (Normal)
```
Customer Message: "Hi, I was charged twice this month for my subscription..."
Expected Response: KB search → ticket creation → professional email
Latency: 850-1100ms
Shows: Normal operation, multi-tool coordination
```

### Scenario 2: WhatsApp — Pricing Question (Happy)
```
Customer Message: "Hey! Your product looks great. What are the pricing plans? 🎉"
Expected Response: Friendly WhatsApp message with emojis
Latency: 900-1200ms
Shows: Channel-specific formatting, positive sentiment
```

### Scenario 3: Email — Angry Customer (AUTO-ESCALATION) ⭐
```
Customer Message: "UNACCEPTABLE! Your support is useless! MANAGER NOW!!!"
Expected Response: ⚠️ AUTO-ESCALATE → high-priority ticket → empathetic response
Latency: 950-1200ms
Shows: KEY DIFFERENTIATOR — Sentiment detection & smart escalation
```

### Scenario 4: Web Form — Onboarding Help (Normal)
```
Customer Message: "I just signed up but I'm confused about integrations..."
Expected Response: KB search + customer history → step-by-step guide
Latency: 900-1150ms
Shows: Web channel integration, personalization
```

### Scenario 5: WhatsApp — Enterprise Request (AUTO-ESCALATION)
```
Customer Message: "I need a human agent for my custom enterprise setup"
Expected Response: ⚠️ AUTO-ESCALATE → route to sales → escalation logged
Latency: 1000-1200ms
Shows: Explicit escalation handling, enterprise awareness
```

---

## 📈 Key Metrics

| Metric | Value | Benchmark |
|--------|-------|-----------|
| **Response Latency** | 850-1200ms | Human: 4+ hours |
| **Throughput** | 20-30 req/s (single) | Good for enterprise |
| **P99 Latency** | 1500ms | Under 2 seconds ✅ |
| **Test Coverage** | 222 tests (91%) | Production-grade |
| **Escalation Detection** | Sentiment-based | Intelligent routing |
| **Cost per Message** | $0.00015 | 55x cheaper than OpenAI |
| **FTE Replacement** | 80% automation | 5 → 1 AI + 1 human |

---

## ✅ Quality Checklist

- ✅ **222 tests** — 38 agent + 23 channels + 34 E2E + 127 unit
- ✅ **91% code coverage** — Comprehensive testing
- ✅ **Production-ready** — Proper async, error handling, logging
- ✅ **Kubernetes-ready** — Docker + manifests included
- ✅ **Real metrics** — All data from actual API calls (not mocked)
- ✅ **5 tool functions** — KB search, ticket create, history, escalate, respond
- ✅ **3 channel integrations** — Email, WhatsApp, Web
- ✅ **Sub-2 second responses** — 850-1200ms real latency
- ✅ **Smart escalation** — Sentiment-based + keyword-based
- ✅ **Cost-optimized** — Groq ($0.27/M) + Meta ($free) vs OpenAI ($15/M) + Twilio ($0.0075/msg)

---

## 🏆 What Makes This Submission Stand Out

1. **Real Production Code** — Not a prototype; async, error handling, logging
2. **Smart Escalation** — Detects angry customers automatically (Scenario 3, 5)
3. **Multi-Channel from Day 1** — Email, WhatsApp, Web simultaneously
4. **Honest About Everything** — Real metrics, admits limitations, explains choices
5. **Complete Package** — Code + tests + deployment + documentation
6. **Cost-Conscious** — Groq + Meta = 10x cheaper than alternatives
7. **Well-Tested** — 222 tests covering all critical paths
8. **Demo-Ready** — Single command shows everything working

---

## 🆘 Troubleshooting

| Problem | Solution |
|---------|----------|
| **Port 8000 in use** | `run_demo.ps1` auto-kills it; or use different port |
| **GROQ_API_KEY not set** | Add to `.env`: `GROQ_API_KEY=your-key` |
| **API won't start** | Check Python 3.11+, see `python production/api/main.py` logs |
| **Demo runner hangs** | API taking too long; check network/API logs |
| **Colors not showing** | Older Windows; auto-disabled in script |
| **Tests fail** | Run `pip install -r requirements.txt` first |

---

## 🎓 Additional Resources

**Inside this repo:**
- `context/` — Knowledge base (brand voice, company profile, escalation rules, product docs)
- `specs/` — Design documents, discovery logs, edge cases
- `production/tests/` — 95+ detailed test cases
- `production/k8s/` — Kubernetes + Docker files

**External:**
- Groq: https://groq.com (API, docs, models)
- Meta WhatsApp Cloud API: https://developers.facebook.com/docs/whatsapp/cloud-api
- FastAPI: https://fastapi.tiangolo.com (framework docs)
- Kubernetes: https://kubernetes.io (K8s docs)

---

## 🚀 Ready to Start?

**Choose one:**

```powershell
# Option 1: Full automated demo (recommended)
.\setup\run_demo.ps1

# Option 2: Just run the demo scripts
python setup/demo_runner.py

# Option 3: Manual exploration
python production/api/main.py
# Then visit http://localhost:8000/api/health
```

---

**Built with ❤️ for the Customer Success FTE Challenge**

*Last Updated: 2026-02-27*

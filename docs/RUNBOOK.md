# NovaDeskAI Incident Response Runbook

## 1. Overview

**Service Name:** NovaDeskAI Customer Success Agent  
**Version:** 2.0.0  
**Environment:** Kubernetes/Docker (production-ready)  
**Primary Function:** AI-powered customer support automation across multiple channels (WhatsApp, Gmail, Web)

### Service Description

NovaDeskAI is a sophisticated customer success platform that processes incoming support requests across multiple communication channels. The system uses an AI agent powered by Groq API to intelligently route, categorize, and respond to customer inquiries. All communication is coordinated through Apache Kafka for reliable message streaming.

### SLA Targets

- **Response Time SLA:** < 2 minutes for initial acknowledgment
- **Uptime Target:** 99.9% availability
- **Message Processing Latency:** < 500ms per message
- **Escalation Time:** < 5 minutes for human handoff

---

## 2. Architecture Quick Reference

### System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                    EXTERNAL CHANNELS                             │
├──────────────────┬──────────────────┬──────────────────┐
│  WhatsApp API    │  Gmail Pub/Sub    │  Web Form        │
│  (443)           │  (443)            │  (443)           │
└────────┬─────────┴────────┬──────────┴────────┬─────────┘
         │                  │                   │
         └──────────────────┼───────────────────┘
                            │ HTTPS/JSON
                            ▼
        ┌─────────────────────────────────────┐
        │     NOVA-API (FastAPI)              │
        │     Port: 8000                      │
        │     /api/messages/process           │
        │     /webhook/whatsapp               │
        │     /webhook/gmail                  │
        └──────────┬────────────┬─────────────┘
                   │            │
        ┌──────────▼──┐  ┌──────▼──────────┐
        │   KAFKA     │  │  CUSTOMER       │
        │   Port 9092 │  │  SUCCESS AGENT  │
        │   (Broker)  │  │  (nova-agent)   │
        └──────┬──────┘  └─────────────────┘
               │
        ┌──────▼──────────────────┐
        │   POSTGRES DB           │
        │   Port 5432             │
        │   (Tickets, History)    │
        └─────────────────────────┘

        ┌─────────────────────────┐
        │   KAFKA-UI              │
        │   Port 8080 (Debug)     │
        └─────────────────────────┘
```

### Service Ports & Connectivity

| Service | Port | Protocol | Purpose |
|---------|------|----------|---------|
| nova-api | 8000 | HTTP | Main API endpoint, webhook receivers |
| nova-mcp | 8001 | HTTP | Model Context Protocol server |
| kafka | 9092 | PLAINTEXT | Message broker (external) |
| kafka | 29092 | PLAINTEXT | Message broker (internal containers) |
| postgres | 5432 | TCP | Database (tickets, conversations) |
| zookeeper | 2181 | TCP | Kafka coordination |
| kafka-ui | 8080 | HTTP | Kafka web interface (debug only) |

### Service Dependencies

```
nova-api depends on:
  ├─ kafka (9092) - message publishing/consuming
  ├─ postgres (5432) - data persistence
  └─ Groq API (https://api.groq.com) - LLM inference

nova-agent depends on:
  ├─ kafka (9092) - message processing
  ├─ Groq API - LLM calls
  └─ External APIs (WhatsApp, Gmail, Groq)

postgres depends on:
  └─ nothing

kafka depends on:
  └─ zookeeper (2181)

zookeeper depends on:
  └─ nothing
```

---

## 3. Severity Levels

### P0 - Critical (Response: 5 minutes, Escalate: Immediately)

**Definition:** System is down, customers cannot send/receive messages, data loss risk

**Indicators:**
- nova-api pod crashing/not starting
- Kafka cluster unavailable
- PostgreSQL connection failure
- All external channels returning 5xx errors
- > 50% message processing failure rate

**Response Actions:**
1. Page on-call engineer immediately
2. Begin incident commander protocol
3. Notify #incident-response channel in Slack
4. Start diagnostics within 2 minutes

---

### P1 - High (Response: 15 minutes, Escalate: 30 minutes)

**Definition:** Major functionality degraded, some customers affected but system partially operational

**Indicators:**
- Single service degraded (one pod down but others running)
- Kafka lag > 10,000 messages
- API latency > 2 seconds
- WhatsApp OR Gmail channel completely down
- Database connections at 80%+ capacity

**Response Actions:**
1. Page on-call engineer
2. Assess impact scope
3. Begin mitigation steps
4. Update status page if SLA impacted

---

### P2 - Medium (Response: 1 hour, Escalate: 2 hours)

**Definition:** Non-critical issues affecting performance or specific features

**Indicators:**
- Single pod restarting frequently
- API latency > 1 second (but < 2 seconds)
- Groq API rate limiting (429 responses)
- Kafka UI inaccessible
- Database disk usage > 80%

**Response Actions:**
1. Notify team lead via email
2. Begin investigation
3. Monitor for escalation
4. Plan fix/mitigation

---

### P3 - Low (Response: Next business day)

**Definition:** Minor issues, no customer impact, informational

**Indicators:**
- Logs contain warnings/deprecations
- Unused resources consuming resources
- Documentation out of date
- Non-critical dependency updates available

**Response Actions:**
1. Log issue in tracker
2. Schedule for next sprint
3. No immediate escalation needed

---

## 4. Common Incidents & Resolution

### Incident 4.1: API Server Down (nova-api Pod Crash)

**Symptoms:**
- `/health` endpoint returns connection refused
- Port 8000 unreachable
- External channels receive timeout errors
- Kubernetes shows pod in CrashLoopBackOff

**Root Causes:**
- Out of memory (OOM)
- Python exception on startup
- Dependency import failure
- Missing environment variables

**Diagnostic Steps:**

```bash
# Check pod status
kubectl -n novadesk get pods -l app=nova-api
kubectl -n novadesk describe pod <pod-name>

# View logs
kubectl -n novadesk logs -f deployment/nova-api --all-containers=true

# Check resource usage
kubectl -n novadesk top pods -l app=nova-api

# Test local connectivity (from inside cluster)
kubectl -n novadesk exec <pod-name> -- curl -v http://localhost:8000/health

# Check environment variables
kubectl -n novadesk get configmap novadesk-config -o yaml
kubectl -n novadesk get secret novadesk-secrets -o yaml
```

**Resolution Steps:**

1. **If OOM (Out of Memory):**
   ```bash
   # Increase memory limits
   kubectl -n novadesk set resources deployment nova-api --limits=memory=2Gi --requests=memory=1Gi
   # Force pod restart
   kubectl -n novadesk rollout restart deployment/nova-api
   ```

2. **If Python/Import Error:**
   ```bash
   # Check logs for traceback
   kubectl -n novadesk logs deployment/nova-api | grep -A 10 "Traceback\|ImportError\|ModuleNotFound"
   
   # Verify all dependencies
   kubectl -n novadesk exec <pod-name> -- pip check
   
   # Rebuild and redeploy
   docker build -t nova-api:latest ./src/api
   kubectl -n novadesk set image deployment/nova-api nova-api=nova-api:latest
   kubectl -n novadesk rollout status deployment/nova-api
   ```

3. **If Environment Variables Missing:**
   ```bash
   # Check if secrets exist
   kubectl -n novadesk get secrets novadesk-secrets
   
   # If missing, recreate
   kubectl -n novadesk create secret generic novadesk-secrets \
     --from-literal=GROQ_API_KEY="<key>" \
     --from-literal=DATABASE_URL="postgresql://nova:novasecret@postgres-service:5432/novadesk"
   
   # Restart deployment
   kubectl -n novadesk rollout restart deployment/nova-api
   ```

**Validation:**
```bash
# Wait for healthy pod
kubectl -n novadesk rollout status deployment/nova-api

# Test health endpoint
kubectl -n novadesk port-forward svc/nova-api 8000:8000 &
curl http://localhost:8000/health

# Test message processing
curl -X POST http://localhost:8000/api/messages/process \
  -H "Content-Type: application/json" \
  -d '{"message":"test","channel":"web","customer_id":"test-cust"}'
```

**Estimated Recovery Time:** 5-10 minutes

---

### Incident 4.2: Kafka Connection Failure

**Symptoms:**
- API logs: `KafkaConnectionError`, `Connection refused on localhost:9092`
- Messages not being published to topics
- Consumer lag not advancing
- nova-agent unable to process messages

**Root Causes:**
- Kafka broker pod down/crashing
- Zookeeper unavailable (Kafka dependency)
- Network connectivity issue
- Kafka advertised listeners misconfigured
- Port 9092 blocked

**Diagnostic Steps:**

```bash
# Check Kafka pod status
kubectl -n novadesk get pods -l app=kafka
kubectl -n novadesk describe pod <kafka-pod>

# Check Zookeeper status
kubectl -n novadesk get pods -l app=zookeeper
kubectl -n novadesk logs deployment/zookeeper | head -50

# Verify Kafka is listening
kubectl -n novadesk exec <kafka-pod> -- nc -zv localhost 29092

# Check Zookeeper connection from Kafka
kubectl -n novadesk logs deployment/kafka | grep -i "zookeeper\|connected"

# List topics (from inside pod)
kubectl -n novadesk exec <kafka-pod> -- kafka-topics --bootstrap-server localhost:29092 --list

# Check broker logs
kubectl -n novadesk logs deployment/kafka -f --tail=100

# Test from API pod
kubectl -n novadesk exec <nova-api-pod> -- python3 -c "
from kafka import KafkaProducer
producer = KafkaProducer(bootstrap_servers='kafka:29092')
producer.send('test-topic', b'test message')
print('Kafka connection OK')
"
```

**Resolution Steps:**

1. **If Kafka Pod Crashed:**
   ```bash
   # Check resource constraints
   kubectl -n novadesk top pods -l app=kafka
   
   # Increase resources if needed
   kubectl -n novadesk set resources deployment kafka --limits=memory=2Gi --requests=memory=1Gi
   
   # Delete pod to restart
   kubectl -n novadesk delete pod -l app=kafka
   
   # Wait for recovery
   kubectl -n novadesk rollout status deployment/kafka -w
   ```

2. **If Zookeeper is Down:**
   ```bash
   # Restart Zookeeper first
   kubectl -n novadesk rollout restart deployment/zookeeper
   kubectl -n novadesk rollout status deployment/zookeeper
   
   # Then restart Kafka
   kubectl -n novadesk rollout restart deployment/kafka
   kubectl -n novadesk rollout status deployment/kafka
   ```

3. **If Configuration Issue:**
   ```bash
   # Check advertised listeners
   kubectl -n novadesk exec <kafka-pod> -- env | grep KAFKA_ADVERTISED
   
   # Verify ConfigMap
   kubectl -n novadesk get configmap novadesk-config -o yaml | grep KAFKA
   
   # Update if needed and redeploy
   kubectl -n novadesk rollout restart deployment/kafka
   ```

**Validation:**
```bash
# Verify Kafka is healthy
kubectl -n novadesk exec <kafka-pod> -- kafka-broker-api-versions --bootstrap-server localhost:29092

# Check topic creation
kubectl -n novadesk exec <kafka-pod> -- kafka-topics --bootstrap-server localhost:29092 --create --topic test-validation --partitions 1 --replication-factor 1 2>/dev/null || echo "Topic exists"

# Send test message
kubectl -n novadesk exec <kafka-pod> -- kafka-console-producer --broker-list localhost:29092 --topic test-validation <<< "test message"

# Consume test message
kubectl -n novadesk exec <kafka-pod> -- kafka-console-consumer --bootstrap-server localhost:29092 --topic test-validation --from-beginning --timeout-ms 5000
```

**Estimated Recovery Time:** 10-15 minutes

---

### Incident 4.3: PostgreSQL Connection Failure

**Symptoms:**
- API logs: `psycopg2.OperationalError: could not connect to server`
- Ticket creation/retrieval fails
- Database timeout errors
- 500 errors on ticket endpoints

**Root Causes:**
- PostgreSQL pod down/crashing
- Database credentials incorrect
- PersistentVolume issue
- Network connectivity to postgres-service
- Disk full

**Diagnostic Steps:**

```bash
# Check PostgreSQL pod
kubectl -n novadesk get pods -l app=postgres
kubectl -n novadesk describe pod <postgres-pod>

# Check logs
kubectl -n novadesk logs deployment/postgres -f --tail=50

# Check PersistentVolume status
kubectl -n novadesk get pvc postgres-pvc
kubectl -n novadesk describe pvc postgres-pvc

# Check disk usage
kubectl -n novadesk exec <postgres-pod> -- df -h /var/lib/postgresql/data

# Test connection from API pod
kubectl -n novadesk exec <nova-api-pod> -- psql -h postgres-service -U nova -d novadesk -c "SELECT 1"

# Check pg_stat_activity (connections)
kubectl -n novadesk exec <postgres-pod> -- psql -U nova -d novadesk -c "SELECT count(*) FROM pg_stat_activity;"

# Verify service DNS resolution
kubectl -n novadesk exec <nova-api-pod> -- nslookup postgres-service
```

**Resolution Steps:**

1. **If PostgreSQL Pod Crashed:**
   ```bash
   # Check resource constraints
   kubectl -n novadesk top pods -l app=postgres
   
   # Increase memory/CPU if needed
   kubectl -n novadesk set resources deployment postgres --limits=memory=2Gi --requests=memory=1Gi
   
   # Restart pod
   kubectl -n novadesk delete pod -l app=postgres
   kubectl -n novadesk rollout status deployment/postgres -w
   ```

2. **If Disk is Full:**
   ```bash
   # Check disk
   kubectl -n novadesk exec <postgres-pod> -- du -sh /var/lib/postgresql/data/*
   
   # Clean old logs/backups if possible
   kubectl -n novadesk exec <postgres-pod> -- find /var/lib/postgresql -name "*.old" -delete
   
   # Expand PVC
   kubectl -n novadesk patch pvc postgres-pvc -p '{"spec":{"resources":{"requests":{"storage":"10Gi"}}}}'
   ```

3. **If Connection Credentials Wrong:**
   ```bash
   # Verify secret
   kubectl -n novadesk get secret novadesk-secrets -o jsonpath='{.data.DATABASE_URL}' | base64 -d
   
   # Recreate secret if needed
   kubectl -n novadesk delete secret novadesk-secrets
   kubectl -n novadesk create secret generic novadesk-secrets \
     --from-literal=DATABASE_URL="postgresql://nova:novasecret@postgres-service:5432/novadesk" \
     --from-literal=POSTGRES_PASSWORD="novasecret"
   
   # Restart postgres
   kubectl -n novadesk rollout restart deployment/postgres
   ```

**Validation:**
```bash
# Test database connection
kubectl -n novadesk exec <postgres-pod> -- psql -U nova -d novadesk -c "SELECT NOW();"

# Check tables exist
kubectl -n novadesk exec <postgres-pod> -- psql -U nova -d novadesk -c "\dt"

# Test from API
curl -X GET http://localhost:8000/api/tickets
```

**Estimated Recovery Time:** 5-10 minutes

---

### Incident 4.4: WhatsApp Webhook 403 Errors

**Symptoms:**
- WhatsApp incoming messages return 403 Forbidden
- Logs: `Invalid verification token` or `Invalid signature`
- Customers report messages not being received
- Webhook test in WhatsApp Business Manager fails

**Root Causes:**
- Webhook URL has changed (IP/domain)
- Verification token doesn't match WhatsApp config
- WHATSAPP_VERIFY_TOKEN environment variable missing/wrong
- WHATSAPP_TOKEN expired or revoked
- Signature validation failing

**Diagnostic Steps:**

```bash
# Check environment variables
kubectl -n novadesk get secret novadesk-secrets -o yaml | grep WHATSAPP

# Verify webhook endpoint is accessible
curl -X GET "http://api.novadesk.local:8000/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=novadesk_verify&hub.challenge=test123"

# Check API logs for webhook errors
kubectl -n novadesk logs deployment/nova-api | grep -i whatsapp

# Verify token matches WhatsApp Business Manager config
# (Manual step: check WhatsApp app settings)

# Test signature validation locally
kubectl -n novadesk exec <nova-api-pod> -- python3 -c "
import hmac
import hashlib
token = 'your-whatsapp-token'
body = '{\"test\": \"data\"}'
signature = 'sha256=' + hmac.new(token.encode(), body.encode(), hashlib.sha256).hexdigest()
print(f'Expected signature: {signature}')
"
```

**Resolution Steps:**

1. **Update Webhook URL in WhatsApp Business Manager:**
   ```bash
   # Get current API endpoint
   kubectl -n novadesk get svc nova-api
   
   # Update in WhatsApp Business Manager:
   # Settings > Configuration > Webhook URL
   # Should be: https://api.yourdomain.com/webhook/whatsapp
   ```

2. **Fix Verification Token:**
   ```bash
   # Get current token from config
   kubectl -n novadesk get configmap novadesk-config -o jsonpath='{.data.WHATSAPP_VERIFY_TOKEN}'
   
   # Update secret to match WhatsApp config
   kubectl -n novadesk patch secret novadesk-secrets -p '{"data":{"WHATSAPP_VERIFY_TOKEN":"'$(echo -n "your-new-token" | base64)'"}}'
   
   # Restart API
   kubectl -n novadesk rollout restart deployment/nova-api
   ```

3. **Verify WHATSAPP_TOKEN is Valid:**
   ```bash
   # Test token with WhatsApp Graph API
   TOKEN=$(kubectl -n novadesk get secret novadesk-secrets -o jsonpath='{.data.WHATSAPP_TOKEN}' | base64 -d)
   
   curl -X GET "https://graph.instagram.com/me?access_token=$TOKEN"
   
   # If 401/403, token is expired - refresh in WhatsApp Business Manager
   ```

**Validation:**
```bash
# Test webhook verification
curl -X GET "http://localhost:8000/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=novadesk_verify&hub.challenge=123456"
# Should return: 123456

# Send test message (simulate WhatsApp webhook)
curl -X POST http://localhost:8000/webhook/whatsapp \
  -H "Content-Type: application/json" \
  -H "X-Hub-Signature-256: sha256=..." \
  -d '{"entry":[{"changes":[{"value":{"messages":[{"from":"1234567890","text":{"body":"test"}}]}}]}]}'
```

**Estimated Recovery Time:** 10-15 minutes

---

### Incident 4.5: Gmail Pub/Sub Not Delivering Messages

**Symptoms:**
- No emails appearing in system
- Gmail webhook endpoint not receiving POST requests
- Logs: `Gmail handler not available` or `ImportError`
- Customers report email backlog

**Root Causes:**
- Gmail Pub/Sub push subscription misconfigured
- Topic/subscription deleted
- Authentication token expired
- Webhook endpoint unreachable
- Gmail handler missing credentials

**Diagnostic Steps:**

```bash
# Check Gmail handler status
kubectl -n novadesk logs deployment/nova-api | grep -i gmail

# Verify Gmail credentials exist
kubectl -n novadesk get secret novadesk-secrets -o yaml | grep -i gmail

# Test webhook endpoint accessibility
curl -X POST http://localhost:8000/webhook/gmail \
  -H "Content-Type: application/json" \
  -d '{"message":{"data":"test"}}'

# Check Pub/Sub subscription status (from local machine with gcloud)
gcloud pubsub subscriptions describe projects/YOUR_PROJECT/subscriptions/novadesk-gmail-sub

# Check push endpoint configuration
gcloud pubsub subscriptions describe projects/YOUR_PROJECT/subscriptions/novadesk-gmail-sub --format='value(pushConfig.pushEndpoint)'

# Test IAM permissions
gcloud pubsub subscriptions get-iam-policy projects/YOUR_PROJECT/subscriptions/novadesk-gmail-sub
```

**Resolution Steps:**

1. **Reconfigure Pub/Sub Push Subscription:**
   ```bash
   # Delete old subscription
   gcloud pubsub subscriptions delete novadesk-gmail-sub
   
   # Create new subscription with correct endpoint
   gcloud pubsub subscriptions create novadesk-gmail-sub \
     --topic=gmail-notifications \
     --push-endpoint=https://api.yourdomain.com/webhook/gmail \
     --push-auth-service-account=nova@YOUR_PROJECT.iam.gserviceaccount.com
   ```

2. **Update Gmail Credentials:**
   ```bash
   # Refresh service account key
   gcloud iam service-accounts keys create gmail-key.json \
     --iam-account=nova@YOUR_PROJECT.iam.gserviceaccount.com
   
   # Update Kubernetes secret
   kubectl -n novadesk create secret generic gmail-credentials \
     --from-file=key.json=gmail-key.json \
     --dry-run=client -o yaml | kubectl apply -f -
   
   # Restart API
   kubectl -n novadesk rollout restart deployment/nova-api
   ```

3. **Verify Webhook Endpoint:**
   ```bash
   # Make sure endpoint is publicly accessible
   curl -v https://api.yourdomain.com/webhook/gmail
   
   # Check DNS resolution
   nslookup api.yourdomain.com
   
   # Verify SSL certificate
   openssl s_client -connect api.yourdomain.com:443
   ```

**Validation:**
```bash
# Send test message to Pub/Sub
gcloud pubsub topics publish gmail-notifications --message='{"test":"data"}'

# Monitor API logs
kubectl -n novadesk logs -f deployment/nova-api | grep gmail

# Check message processing endpoint
curl http://localhost:8000/api/messages/process -X POST \
  -H "Content-Type: application/json" \
  -d '{"message":"test email","channel":"gmail","customer_id":"test"}'
```

**Estimated Recovery Time:** 15-20 minutes

---

### Incident 4.6: Groq API Rate Limiting (429)

**Symptoms:**
- Agent responses: `429 Too Many Requests`
- Logs: `RateLimitError`, `quota exceeded`
- Response latency increases dramatically
- Some messages fail to process

**Root Causes:**
- API key quota exceeded
- Too many concurrent requests to Groq
- Usage spike beyond plan limits
- API key rate limit reset pending
- Model endpoint overloaded

**Diagnostic Steps:**

```bash
# Check Groq API errors
kubectl -n novadesk logs deployment/nova-api | grep -i "429\|rate.limit\|quota"

# Check current request rate
kubectl -n novadesk logs deployment/nova-api --tail=1000 | grep -i groq | wc -l

# Verify API key is valid
TOKEN=$(kubectl -n novadesk get secret novadesk-secrets -o jsonpath='{.data.GROQ_API_KEY}' | base64 -d)
curl -X GET "https://api.groq.com/openai/v1/models" \
  -H "Authorization: Bearer $TOKEN"

# Monitor Groq API status
curl -s https://status.groq.com/api/v2/status.json | jq '.components[] | select(.name | contains("API"))'
```

**Resolution Steps:**

1. **Reduce Request Load (Immediate):**
   ```bash
   # Scale down API replicas temporarily
   kubectl -n novadesk scale deployment nova-api --replicas=1
   
   # This reduces concurrent Groq API calls
   # Monitor for queue buildup
   ```

2. **Upgrade Groq API Plan:**
   ```bash
   # Contact Groq support or upgrade plan at console.groq.com
   # Increase rate limit from default (e.g., 100 req/min to 1000 req/min)
   
   # Wait 5-10 minutes for new limits to take effect
   ```

3. **Implement Request Queuing:**
   ```bash
   # Update nova-api deployment with rate limiter
   # (Add slowdown/backoff logic)
   
   # Temporarily use slower model if available
   kubectl -n novadesk set env deployment/nova-api GROQ_MODEL="mixtral-8x7b"
   ```

4. **Scale Back Up:**
   ```bash
   # Once rate limit issue resolved
   kubectl -n novadesk scale deployment nova-api --replicas=3
   kubectl -n novadesk rollout status deployment/nova-api
   ```

**Validation:**
```bash
# Test Groq API availability
curl -X POST https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"mixtral-8x7b-instant","messages":[{"role":"user","content":"test"}],"max_tokens":10}'

# Monitor response codes
kubectl -n novadesk logs deployment/nova-api -f | grep "200\|429\|500"
```

**Estimated Recovery Time:** 5-30 minutes (depends on plan upgrade)

---

### Incident 4.7: High Latency / Slow Responses

**Symptoms:**
- Message processing takes > 2 seconds
- Customers report slow reply times
- Logs: `latency_ms: 3000+`
- API /health endpoint slow to respond

**Root Causes:**
- Kafka lag (messages not being processed)
- PostgreSQL queries slow
- Groq API response times high
- Pod resource exhaustion (CPU/memory)
- Network congestion
- Database lock contention

**Diagnostic Steps:**

```bash
# Check API latency
kubectl -n novadesk logs deployment/nova-api | grep latency_ms | tail -20

# Monitor pod resource usage
kubectl -n novadesk top pods --all-containers=true

# Check Kafka consumer lag
kubectl -n novadesk exec <kafka-pod> -- kafka-consumer-groups --bootstrap-server localhost:29092 --group nova-agent-group --describe

# Check database connections
kubectl -n novadesk exec <postgres-pod> -- psql -U nova -d novadesk -c "SELECT count(*), state FROM pg_stat_activity GROUP BY state;"

# Check Groq API response times
kubectl -n novadesk logs deployment/nova-api | grep -i groq | tail -30

# Monitor network traffic
kubectl -n novadesk exec <nova-api-pod> -- ss -an | grep ESTABLISHED | wc -l

# Check Pod QoS class
kubectl -n novadesk get pods <pod-name> -o jsonpath='{.status.qosClass}'
```

**Resolution Steps:**

1. **Increase Pod Resources:**
   ```bash
   # Increase memory/CPU limits
   kubectl -n novadesk set resources deployment nova-api \
     --limits=cpu=2,memory=2Gi \
     --requests=cpu=500m,memory=1Gi
   
   # Restart pods
   kubectl -n novadesk rollout restart deployment/nova-api
   ```

2. **Scale Out API Pods:**
   ```bash
   # Increase replicas
   kubectl -n novadesk scale deployment nova-api --replicas=5
   
   # Verify load balancing
   kubectl -n novadesk get endpoints nova-api
   ```

3. **Optimize Database Queries:**
   ```bash
   # Check slow query log
   kubectl -n novadesk exec <postgres-pod> -- psql -U nova -d novadesk -c "SELECT * FROM pg_stat_statements ORDER BY mean_time DESC LIMIT 10;"
   
   # Add indexes if needed
   kubectl -n novadesk exec <postgres-pod> -- psql -U nova -d novadesk -c "CREATE INDEX idx_ticket_status ON tickets(status);"
   ```

4. **Reduce Kafka Lag:**
   ```bash
   # Check consumer group status
   kubectl -n novadesk exec <kafka-pod> -- kafka-consumer-groups --bootstrap-server localhost:29092 --group nova-agent-group --describe
   
   # If lag > 10k, scale nova-agent workers
   kubectl -n novadesk scale deployment nova-agent --replicas=5
   ```

5. **Check Groq API Status:**
   ```bash
   # Verify Groq service availability
   curl -s https://status.groq.com/api/v2/status.json | jq '.status.indicator'
   
   # If degraded, wait or use fallback model
   ```

**Validation:**
```bash
# Re-test message processing latency
time curl -X POST http://localhost:8000/api/messages/process \
  -H "Content-Type: application/json" \
  -d '{"message":"test","channel":"web","customer_id":"test"}'

# Monitor logs for improved latency
kubectl -n novadesk logs deployment/nova-api -f | grep latency_ms | tail -5

# Verify pod CPU/memory normalized
kubectl -n novadesk top pods --all-containers=true
```

**Estimated Recovery Time:** 5-15 minutes

---

### Incident 4.8: Agent Returning Error Responses

**Symptoms:**
- Agent responses: `Error processing request: ...`
- Empty or null responses
- Logs: `Agent error:`, `Exception in agent.run()`
- Tool execution failures

**Root Causes:**
- Agent initialization failed
- Groq API connection error
- Missing context/knowledge files
- Tool execution error
- Agent configuration corrupted

**Diagnostic Steps:**

```bash
# Check agent logs
kubectl -n novadesk logs deployment/nova-api | grep -i "agent error\|exception"

# Verify agent imports
kubectl -n novadesk exec <nova-api-pod> -- python3 -c "from production.agent.customer_success_agent import CustomerSuccessAgent; print('OK')"

# Check if agent is initialized
kubectl -n novadesk exec <nova-api-pod> -- python3 -c "import sys; sys.path.insert(0, '/app'); from production.agent.customer_success_agent import CustomerSuccessAgent; agent = CustomerSuccessAgent(); print(f'Agent initialized: {agent is not None}')"

# Verify context files exist
kubectl -n novadesk exec <nova-api-pod> -- ls -la /app/context/

# Test Groq API directly
TOKEN=$(kubectl -n novadesk get secret novadesk-secrets -o jsonpath='{.data.GROQ_API_KEY}' | base64 -d)
curl -X POST https://api.groq.com/openai/v1/chat/completions \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"model":"mixtral-8x7b-instant","messages":[{"role":"user","content":"hi"}],"max_tokens":100}'
```

**Resolution Steps:**

1. **Restart Agent:**
   ```bash
   # Force pod restart
   kubectl -n novadesk delete pod -l app=nova-api
   kubectl -n novadesk rollout status deployment/nova-api
   ```

2. **Verify Configuration:**
   ```bash
   # Check all required secrets
   kubectl -n novadesk get secret novadesk-secrets -o yaml
   
   # Check ConfigMap
   kubectl -n novadesk get configmap novadesk-config -o yaml
   
   # Update if missing
   kubectl -n novadesk set env deployment/nova-api \
     GROQ_API_KEY=$(kubectl get secret novadesk-secrets -o jsonpath='{.data.GROQ_API_KEY}' | base64 -d)
   ```

3. **Check Context Files:**
   ```bash
   # Verify all context files present
   kubectl -n novadesk exec <nova-api-pod> -- find /app/context -type f
   
   # If missing, redeploy with updated image
   docker build -t nova-api:latest ./src/api
   kubectl -n novadesk set image deployment/nova-api nova-api=nova-api:latest --record
   ```

4. **Review Agent Logs:**
   ```bash
   # Get detailed error trace
   kubectl -n novadesk logs deployment/nova-api --tail=100 | grep -A 20 "Traceback"
   
   # Fix agent code if needed and rebuild
   ```

**Validation:**
```bash
# Test message processing directly
curl -X POST http://localhost:8000/api/messages/process \
  -H "Content-Type: application/json" \
  -d '{"message":"help me","channel":"web","customer_id":"test"}'

# Should return proper response, not error
```

**Estimated Recovery Time:** 5-10 minutes

---

## 5. Diagnostic Commands Quick Reference

### Kubernetes Health Checks

```bash
# Check all pods in novadesk namespace
kubectl -n novadesk get pods -o wide

# Get detailed pod info (useful for debugging)
kubectl -n novadesk describe pod <pod-name>

# View pod logs (real-time)
kubectl -n novadesk logs -f deployment/<deployment-name>

# Logs from all containers in a deployment
kubectl -n novadesk logs deployment/<deployment-name> --all-containers=true --timestamps=true

# Get previous logs (if pod crashed)
kubectl -n novadesk logs <pod-name> --previous

# Execute command inside pod
kubectl -n novadesk exec <pod-name> -- <command>

# Get pod resource usage
kubectl -n novadesk top pods --all-containers=true

# Get node resource usage
kubectl -n novadesk top nodes

# Describe a service
kubectl -n novadesk describe svc <service-name>

# Get endpoints (real pod IPs backing service)
kubectl -n novadesk get endpoints <service-name>

# Check deployment rollout status
kubectl -n novadesk rollout status deployment/<deployment-name> -w

# View deployment history
kubectl -n novadesk rollout history deployment/<deployment-name>

# Get ConfigMap
kubectl -n novadesk get configmap novadesk-config -o yaml

# Get Secrets (base64 encoded)
kubectl -n novadesk get secret novadesk-secrets -o yaml
```

### API Health Checks (Port 8000)

```bash
# Health check endpoint
curl -v http://localhost:8000/health

# Root endpoint
curl http://localhost:8000/

# API docs (Swagger UI)
curl http://localhost:8000/docs

# Test message processing
curl -X POST http://localhost:8000/api/messages/process \
  -H "Content-Type: application/json" \
  -d '{
    "message": "test message",
    "channel": "web",
    "customer_id": "test-customer-123"
  }'

# List all tickets
curl http://localhost:8000/api/tickets

# Get ticket stats
curl http://localhost:8000/api/stats

# Get metrics
curl http://localhost:8000/api/metrics

# Port forward to access API from localhost
kubectl -n novadesk port-forward svc/nova-api 8000:8000 &
```

### Kafka Diagnostics (Port 9092)

```bash
# Check Kafka broker status from inside pod
kubectl -n novadesk exec <kafka-pod> -- kafka-broker-api-versions --bootstrap-server localhost:29092

# List all topics
kubectl -n novadesk exec <kafka-pod> -- kafka-topics --bootstrap-server localhost:29092 --list

# Describe a topic
kubectl -n novadesk exec <kafka-pod> -- kafka-topics --bootstrap-server localhost:29092 --describe --topic <topic-name>

# Check consumer groups
kubectl -n novadesk exec <kafka-pod> -- kafka-consumer-groups --bootstrap-server localhost:29092 --list

# Check consumer group status/lag
kubectl -n novadesk exec <kafka-pod> -- kafka-consumer-groups --bootstrap-server localhost:29092 --group nova-agent-group --describe

# Monitor topic in real-time
kubectl -n novadesk exec <kafka-pod> -- kafka-console-consumer --bootstrap-server localhost:29092 --topic <topic-name> --from-beginning --timeout-ms 5000

# Produce test message
kubectl -n novadesk exec <kafka-pod> -- kafka-console-producer --broker-list localhost:29092 --topic test-topic <<< "test message"

# Check Zookeeper connection
kubectl -n novadesk exec <kafka-pod> -- echo ruok | nc localhost 2181

# View Kafka logs
kubectl -n novadesk logs deployment/kafka -f --tail=100
```

### PostgreSQL Diagnostics (Port 5432)

```bash
# Connect to PostgreSQL from inside pod
kubectl -n novadesk exec <postgres-pod> -- psql -U nova -d novadesk

# Query examples once connected:
SELECT NOW();  -- Test connection
\dt            -- List tables
SELECT COUNT(*) FROM tickets;  -- Count tickets
SELECT * FROM tickets LIMIT 5;  -- View sample tickets

# Check active connections
kubectl -n novadesk exec <postgres-pod> -- psql -U nova -d novadesk -c "SELECT count(*) FROM pg_stat_activity;"

# Check long-running queries
kubectl -n novadesk exec <postgres-pod> -- psql -U nova -d novadesk -c "SELECT pid, usename, state, query_start, query FROM pg_stat_activity WHERE state != 'idle';"

# Check disk usage
kubectl -n novadesk exec <postgres-pod> -- du -sh /var/lib/postgresql/data

# List databases
kubectl -n novadesk exec <postgres-pod> -- psql -U nova -c "\l"

# Backup database
kubectl -n novadesk exec <postgres-pod> -- pg_dump -U nova novadesk > backup.sql

# Check PVC status
kubectl -n novadesk get pvc postgres-pvc -o wide

# Describe PVC for capacity info
kubectl -n novadesk describe pvc postgres-pvc
```

### Docker Compose (Local/Dev Testing)

```bash
# Start all services
docker-compose up -d

# View logs for specific service
docker-compose logs -f nova-api

# Check service health
docker-compose ps

# Execute command in container
docker-compose exec nova-api curl http://localhost:8000/health

# Stop all services
docker-compose down

# Restart a service
docker-compose restart nova-api

# View resource usage
docker stats
```

---

## 6. Escalation Matrix

### By Incident Type

| Incident Type | P0/P1 | P2 | Escalation Path |
|---|---|---|---|
| API Pod Crash | Page On-Call | Email Team | On-Call Eng → Tech Lead → CTO |
| Kafka Broker Down | Page On-Call | Email Team | On-Call Eng → Infra Lead |
| Database Connection Failure | Page On-Call | Email Team | On-Call Eng → DBA → CTO |
| WhatsApp Webhook Failure | Email Team | Ticket | Support Team → On-Call Eng |
| Gmail Delivery Failure | Email Team | Ticket | Support Team → GCP Specialist |
| Groq API Rate Limiting | Email Team | Ticket | Support Team → On-Call Eng → Groq Support |
| High Latency | Email Team | Ticket | On-Call Eng → Performance Team |
| Agent Errors | Email Team | Ticket | On-Call Eng → Agent Dev Lead |

### On-Call Contact Information

**Primary On-Call Engineer**
- Slack: `@on-call` in #incident-response
- PagerDuty: Escalation policy "NovaDeskAI-Primary"
- Phone: Configured in PagerDuty

**Secondary On-Call (if Primary Unavailable)**
- Slack: `@on-call-secondary`
- PagerDuty: Escalation policy "NovaDeskAI-Secondary"

**Team Leads by Function**

| Function | Name | Slack | On-Call |
|---|---|---|---|
| Backend Engineering | TBD | @backend-lead | Mon-Wed |
| Infrastructure | TBD | @infra-lead | Thu-Fri, weekends |
| Database | TBD | @dba-lead | On-demand |
| Support | TBD | @support-lead | Business hours |

**External Escalation**

| Service | Contact Method | SLA |
|---|---|---|
| Groq API Support | support@groq.com | 1 hour |
| Google Cloud Support | support.google.com | 1 hour (Premium) |
| WhatsApp Business Support | business-support@whatsapp.com | 24 hours |
| Kafka Community | Apache Kafka Slack | Best effort |

### Escalation Criteria

**Escalate to Tech Lead if:**
- Incident unresolved after 15 minutes of on-call engagement
- Multiple systems affected simultaneously
- Data loss or corruption likely
- Customer communication needed

**Escalate to CTO if:**
- Incident duration > 1 hour
- Revenue impact > $10k/hour
- Public incident (social media/press)
- Requires architectural decision

---

## 7. Recovery Procedures

### Standard Recovery Process

1. **Assess** (0-5 min)
   - Is this P0, P1, P2, or P3?
   - How many customers affected?
   - What is the scope of impact?

2. **Stabilize** (5-15 min)
   - Apply immediate mitigation (restart pods, scale down, etc.)
   - Stop the bleeding (prevent data loss, further escalation)
   - Communicate status to team

3. **Investigate** (15-60 min)
   - Gather logs, metrics, error messages
   - Identify root cause
   - Document findings

4. **Implement** (30-120 min)
   - Apply permanent fix (code change, config update, etc.)
   - Test in staging if possible
   - Deploy to production with rollback plan

5. **Validate** (10-30 min)
   - Verify fix works
   - Monitor metrics/logs
   - Confirm customer impact resolved

6. **Communicate** (ongoing)
   - Keep stakeholders updated every 15 min
   - Post-incident: send RCA to team

### Recovery for Common Scenarios

#### Scenario: Pod OOM (Out of Memory)

```bash
# 1. Immediate mitigation
kubectl -n novadesk set resources deployment nova-api --limits=memory=2Gi
kubectl -n novadesk rollout restart deployment/nova-api
kubectl -n novadesk rollout status deployment/nova-api -w

# 2. Investigate
kubectl -n novadesk top pods --sort-by=memory

# 3. Long-term fix (depends on finding)
# - If code memory leak: fix code, rebuild image
# - If normal usage: increase resource request/limit permanently
# - If spike: investigate spike cause (bad query, etc.)

# 4. Validate
kubectl -n novadesk exec <nova-api-pod> -- curl http://localhost:8000/health
```

#### Scenario: Database Connection Exhaustion

```bash
# 1. Immediate mitigation
kubectl -n novadesk scale deployment nova-api --replicas=1  # Reduce connections
kubectl -n novadesk rollout status deployment/nova-api

# 2. Investigate
kubectl -n novadesk exec <postgres-pod> -- psql -U nova -d novadesk -c "SELECT count(*) FROM pg_stat_activity;"

# 3. Fix (choose based on investigation)
# Option A: Increase pool size in API
kubectl -n novadesk set env deployment/nova-api DB_POOL_SIZE=50

# Option B: Kill long-running queries
kubectl -n novadesk exec <postgres-pod> -- psql -U nova -d novadesk -c "SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE state='idle' AND query_start < NOW() - INTERVAL '10 minutes';"

# 4. Scale back up
kubectl -n novadesk scale deployment nova-api --replicas=3
```

#### Scenario: Kafka Consumer Lag Building Up

```bash
# 1. Check lag
kubectl -n novadesk exec <kafka-pod> -- kafka-consumer-groups --bootstrap-server localhost:29092 --group nova-agent-group --describe

# 2. If lag > 50k messages:
# Option A: Scale nova-agent workers
kubectl -n novadesk scale deployment nova-agent --replicas=10

# Option B: Temporarily pause API to let agent catch up
kubectl -n novadesk scale deployment nova-api --replicas=0
sleep 300
kubectl -n novadesk scale deployment nova-api --replicas=3

# 3. Monitor lag decreasing
kubectl -n novadesk exec <kafka-pod> -- kafka-consumer-groups --bootstrap-server localhost:29092 --group nova-agent-group --describe
```

#### Scenario: External API Failure (Groq, WhatsApp, Gmail)

```bash
# 1. Verify issue is external
curl https://status.groq.com  # Check status page

# 2. For Groq rate limiting: scale down
kubectl -n novadesk scale deployment nova-api --replicas=1

# 3. For external API down: failover options
# - Return queued response to customer (if available)
# - Queue message for later processing
# - Return "service temporarily unavailable" message

# 4. Monitor status page
# When external API recovers, scale back up
kubectl -n novadesk scale deployment nova-api --replicas=3
```

---

## 8. Monitoring & Alerts

### Key Metrics to Watch

**System Health**
- Pod restart count (any restarts = potential issue)
- Pod CPU/memory usage (sustained > 80% = warning)
- Pod QoS class (Burstable/BestEffort = worse than Guaranteed)
- PVC usage (> 80% full = warning, > 95% = critical)

**API Performance**
- Response latency (p50 < 500ms, p99 < 2s ideal)
- Error rate (should be < 1%)
- Request rate (track baseline for anomalies)
- Active connections (spikes indicate traffic surge)

**Kafka**
- Consumer lag per group (< 1000 msgs = healthy)
- Topic partition replication (should be 100% in-sync)
- Broker disk usage (< 70% = healthy)
- Producer error rate (should be 0%)

**Database**
- Connection count (< 80% of max pool)
- Active queries (none running > 5 min)
- Slow query count (query time > 1s should be rare)
- Disk usage (< 80% = healthy)

**External Services**
- Groq API response time (usually < 2s)
- Groq 429 rate limit errors (should be 0)
- WhatsApp webhook delivery success rate (> 99%)
- Gmail Pub/Sub delivery latency (< 1 min)

### Alert Thresholds

| Metric | Warning Threshold | Critical Threshold | Check Frequency |
|---|---|---|---|
| Pod CPU | > 1000m (50% limit) | > 1500m (75% limit) | Every 1 min |
| Pod Memory | > 1GB (50% limit) | > 1.5GB (75% limit) | Every 1 min |
| API Latency (p99) | > 1.5s | > 3s | Every 1 min |
| API Error Rate | > 5% | > 10% | Every 1 min |
| Kafka Consumer Lag | > 5000 msgs | > 50000 msgs | Every 5 min |
| DB Connections | > 60 | > 80 | Every 1 min |
| DB Disk Usage | > 70% | > 90% | Every 5 min |
| PVC Usage | > 70% | > 90% | Every 5 min |
| Groq 429 Errors | > 1% | > 5% | Every 1 min |

### Grafana/Prometheus Queries (Examples)

```promql
# API error rate in last 5 minutes
rate(api_errors_total[5m])

# Pod memory usage
container_memory_usage_bytes{namespace="novadesk"}

# Pod CPU usage
rate(container_cpu_usage_seconds_total{namespace="novadesk"}[1m])

# API response latency (p99)
histogram_quantile(0.99, rate(api_response_duration_seconds_bucket[5m]))

# Kafka consumer lag
kafka_consumer_lag{group="nova-agent-group"}

# Database connections
pg_stat_activity_count{state="active"}
```

---

## 9. Post-Incident Checklist

After resolving any P0 or P1 incident, complete this checklist:

### Immediate Actions (Within 2 hours)

- [ ] **Notify stakeholders** via email with incident summary
- [ ] **Check customer impact** - contact affected customers if needed
- [ ] **Verify fix is stable** - monitor for 30+ minutes with no issues
- [ ] **Document timeline** - when incident started, when resolved, duration
- [ ] **Backup any logs** - save logs from Kubernetes, database, external services

### Root Cause Analysis (Within 24 hours)

- [ ] **Identify root cause** - what actually went wrong?
- [ ] **Why did it happen?** - missing validation, inadequate testing, etc.
- [ ] **Why wasn't it caught?** - monitoring gap, alert threshold too high, etc.
- [ ] **Assign action items** - who will fix, by when?
- [ ] **Document RCA** - create incident report (see template below)

### Preventive Measures (Within 1 week)

- [ ] **Implement permanent fix** - code change, config update, dependency upgrade
- [ ] **Add monitoring/alerts** - for this issue to prevent recurrence
- [ ] **Add test case** - unit/integration test to catch this in future
- [ ] **Update documentation** - runbook, architecture docs, etc.
- [ ] **Conduct postmortem** - team discussion (blameless, learning-focused)

### RCA Report Template

```markdown
## Incident Report: [SERVICE] - [DATE]

### Summary
- **Duration:** [Start time] to [End time] ([Total minutes])
- **Impact:** [X% of users affected, $Y revenue impact, Z messages lost]
- **Severity:** P0 / P1 / P2 / P3

### Timeline
- 14:32 - Alert triggered: High API latency
- 14:35 - On-call engineer started investigating
- 14:42 - Root cause identified: OOM on nova-api pod
- 14:48 - Memory limit increased from 1GB to 2GB
- 14:50 - Pods restarted, services recovered
- 14:55 - Verified recovery, monitoring shows normal latency

### Root Cause
The nova-api pod ran out of memory due to a memory leak in the message processing loop. Each processed message added ~50KB to memory that was never released, causing OOM after ~20k messages.

### Why It Happened
1. Lack of memory profiling in CI/CD pipeline
2. No load testing before deployment
3. Memory limit was set based on development testing (only 10 msgs/sec)

### Why It Wasn't Caught
1. Alert threshold for memory was at 90%, incident happened at 95%
2. Alert had 5-minute evaluation period, pod crashed before alert fired
3. No pre-deployment capacity planning review

### Action Items
| Item | Owner | Due Date |
|------|-------|----------|
| Fix memory leak in message processor | @alice | 2025-01-20 |
| Add memory profiling to CI/CD | @bob | 2025-01-20 |
| Run load test before deployments | @charlie | 2025-01-25 |
| Lower memory alert threshold to 70% | @diana | 2025-01-17 |
| Reduce alert evaluation period to 1 min | @diana | 2025-01-17 |
```

---

## 10. Contact & On-Call Information

### Primary Contacts

**On-Call Schedule**
- Schedule URL: [YOUR_PAGERDUTY_SCHEDULE_URL]
- Slack Channel: #incident-response (all incidents posted here)
- Status Page: [YOUR_STATUS_PAGE_URL] (public incident tracking)

### Team Roster

**Platform & Infrastructure**
- Tech Lead: [Name] - [Phone] - [Email]
- Senior Eng: [Name] - [Phone] - [Email]
- DevOps Engineer: [Name] - [Phone] - [Email]

**Application Engineering**
- Agent Lead: [Name] - [Phone] - [Email]
- Backend Lead: [Name] - [Phone] - [Email]

**Customer Success**
- Support Manager: [Name] - [Phone] - [Email]
- Support Team: [Email group]

### Emergency Numbers

| Role | Number | Available |
|------|--------|-----------|
| On-Call Primary | +1-XXX-XXX-XXXX | 24/7 (PagerDuty) |
| On-Call Secondary | +1-XXX-XXX-XXXX | 24/7 (PagerDuty) |
| Tech Lead | +1-XXX-XXX-XXXX | Business hours + on-call |
| CTO | +1-XXX-XXX-XXXX | Critical incidents only |

### Slack Communities for Help

- `#incident-response` - All incidents posted here
- `#engineering` - General engineering questions
- `#devops` - Infrastructure/deployment questions
- `#database` - Database questions
- `#api-clients` - Customer API integration help

### External Support Contacts

**Groq API**
- Support Portal: console.groq.com/support
- Email: support@groq.com
- Community Slack: [Groq Community]
- Response SLA: 1 hour for premium

**Google Cloud (Gmail/Pub/Sub)**
- Support Portal: console.cloud.google.com/support
- Email: support@google.com
- Community: Stack Overflow [google-cloud-platform tag]
- Response SLA: 1 hour for premium

**WhatsApp Business**
- Support Portal: business.facebook.com/support
- Email: business-support@whatsapp.com
- Response SLA: 24 hours

**Kafka**
- Community Slack: confluentinc/community-slack
- Apache JIRA: issues.apache.org/jira/browse/KAFKA
- Community Forums: stackoverflow.com [apache-kafka tag]

### Useful Runbook Links

- [NovaDeskAI Architecture Docs](./ARCHITECTURE.md)
- [Deployment Guide](./DEPLOYMENT.md)
- [API Documentation](./API.md)
- [Kubernetes Setup](./production/k8s/README-k8s.md)
- [Groq API Docs](https://console.groq.com/docs/api-overview)
- [Kafka Documentation](https://kafka.apache.org/documentation/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)

### Incident Communication Template

When posting incident to Slack `#incident-response`:

```
🚨 **INCIDENT: [Service Name] - [Severity: P0/P1/P2]**

**Status:** Investigating / Mitigating / Resolved

**Duration:** [Start time] - [Current time] ([Minutes elapsed])

**Impact:** [Brief description of what's broken]

**Affected Users:** [Number/percentage of users affected]

**Current Actions:** [What the on-call engineer is doing right now]

**ETA to Resolution:** [Best estimate]

**Updates:** 
- 14:32 UTC - Incident detected, on-call paged
- 14:38 UTC - Root cause identified
- [Ongoing updates every 15 min]
```

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-01-15 | DevOps Team | Initial runbook creation |

---

**Last Updated:** 2025-01-15  
**Next Review:** 2025-04-15 (quarterly)  
**Maintainer:** DevOps Team


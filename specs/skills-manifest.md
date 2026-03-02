# Skills Manifest: Nova Customer Success AI Agent

**Version**: 1.0.0  
**Agent Name**: Nova  
**Last Updated**: 2026-02-27  
**Status**: Specification Phase

---

## Overview

Nova is equipped with a modular skill system enabling intelligent customer support across email, WhatsApp, and web channels. Each skill is independently versioned, monitored, and can be toggled on/off without redeployment. Skills are composed of LLM calls, rules engines, and tool integrations.

---

## Skill Definitions

### Skill: `knowledge_retrieval`

**Version**: 1.0.0  
**Category**: Information Retrieval  
**SLA**: <500ms response time

#### Description
Searches and retrieves relevant product documentation, FAQs, and knowledge base articles based on customer query. Returns ranked results with confidence scores to determine if answer quality is sufficient for autonomous response or requires escalation.

#### Inputs
```json
{
  "query": "string (customer question/issue description)",
  "channel": "string (enum: email | whatsapp | web)",
  "conversation_history": "array of messages (optional, provides context)",
  "customer_segment": "string (enum: free | pro | enterprise)",
  "language": "string (default: en, future: es, fr, de)"
}
```

#### Outputs
```json
{
  "results": [
    {
      "doc_id": "string",
      "title": "string",
      "excerpt": "string (first 200 chars)",
      "url": "string",
      "confidence_score": "number (0.0-1.0)",
      "relevance_rank": "integer (1-n)",
      "category": "string",
      "last_updated": "ISO8601 timestamp"
    }
  ],
  "best_result_confidence": "number (0.0-1.0)",
  "query_understood": "boolean",
  "alternative_queries_suggested": "array of strings (if confidence < 0.7)",
  "search_duration_ms": "integer"
}
```

#### Triggers
- Customer submits a question or describes a problem
- Agent needs to validate answer before responding
- Escalation requires "reason for escalation" with KB search evidence

#### Implementation Details
- **Tool Used**: `search_knowledge_base` (custom MCP tool)
- **Backend**: Vector similarity search (embeddings) + BM25 keyword matching
- **Fallback Strategy**: 
  - If confidence < 0.6: Escalate with result to human for validation
  - If no results found: Route to escalation pipeline with "no KB match" flag
  - If multiple equally confident results: Return top 3 and let downstream skill decide

#### Confidence Thresholds
| Confidence Range | Action |
|------------------|--------|
| 0.85-1.0 | Autonomous response (cite source) |
| 0.70-0.84 | Autonomous response with disclaimer ("based on our docs") |
| 0.60-0.69 | Flag for human review before sending |
| <0.60 | Escalate, do not respond autonomously |

#### Monitoring
- Track: hit rate, avg confidence, FCR correlation
- Alert if: confidence < 0.65 for >5% of queries, search duration >1000ms

---

### Skill: `sentiment_analysis`

**Version**: 1.0.0  
**Category**: NLP / Understanding  
**SLA**: <200ms response time

#### Description
Analyzes customer message text and conversation history to detect emotional tone and sentiment. Outputs structured sentiment label with confidence score and detailed emotional indicators. Triggers escalation pipeline if anger or extreme frustration detected.

#### Inputs
```json
{
  "message_text": "string (current customer message)",
  "conversation_history": "array of {role: string, text: string, timestamp: ISO8601}",
  "channel": "string (email | whatsapp | web)",
  "prior_sentiment_scores": "array of numbers (optional, for trend detection)"
}
```

#### Outputs
```json
{
  "sentiment_label": "string (enum: positive | neutral | frustrated | angry)",
  "sentiment_score": "number (0.0-1.0, where 0=most negative, 1=most positive)",
  "confidence": "number (0.0-1.0)",
  "emotional_indicators": {
    "frustration_level": "number (0.0-1.0)",
    "urgency_detected": "boolean",
    "sarcasm_detected": "boolean",
    "all_caps_detected": "boolean",
    "exclamation_count": "integer",
    "question_mark_count": "integer",
    "has_curse_words": "boolean",
    "previous_attempts_mentioned": "boolean"
  },
  "trend": "string (enum: escalating | stable | de_escalating | unknown)",
  "suggested_response_tone": "string (enum: empathetic | professional | casual | urgent_acknowledgment)"
}
```

#### Triggers
- Every inbound customer message (trigger sentiment analysis immediately)
- Escalation decision point (re-analyze if borderline)
- Emotional_indicators.frustration_level > 0.7 → trigger escalation pipeline
- sentiment_label = "angry" → immediate escalation with priority override

#### Implementation Details
- **Model Used**: Groq llama-3.3-70b-versatile
- **Prompt Strategy**: Few-shot examples from discovery log + conversation context
- **Language Support**: English (v1.0), Spanish/French (future)
- **Latency Target**: 80-150ms per analysis

#### Confidence Thresholds
| Confidence | Action |
|------------|--------|
| >0.90 | Strong signal, weight heavily in decisions |
| 0.75-0.89 | Standard signal, use in combination with other factors |
| 0.60-0.74 | Weak signal, flag as ambiguous |
| <0.60 | Defer sentiment-based decision to escalation rules |

#### Special Cases
- **Sarcasm Detection**: If sarcasm_detected = true AND sentiment_label = positive, re-evaluate (likely frustrated)
- **Trend Analysis**: If escalating sentiment across 2+ messages, trigger escalation automatically
- **Language Mixing**: Messages mixing English with casual abbreviations handled via WhatsApp-specific classifier

#### Monitoring
- Track: misclassification rate vs. manual labels, sentiment drift over time
- Alert if: angry sentiment not followed by escalation within 2 min

---

### Skill: `escalation_decision`

**Version**: 1.0.0  
**Category**: Business Logic / Routing  
**SLA**: <300ms response time

#### Description
Determines whether customer issue requires escalation to human support and at which tier (1, 2, or 3). Uses combination of rules-based logic, sentiment signals, and LLM override capability. Ensures high-priority and frustrated customers reach appropriate human agents quickly.

#### Inputs
```json
{
  "sentiment_score": "number (0.0-1.0)",
  "sentiment_label": "string (positive | neutral | frustrated | angry)",
  "priority": "string (P1 | P2 | P3 | P4)",
  "failed_attempts": "integer (number of times this issue addressed autonomously)",
  "sla_breach_imminent": "boolean (time_remaining < 25% of SLA)",
  "customer_request_explicit": "string (enum: null | human_agent | manager | supervisor)",
  "issue_category": "string (integrations | billing | config | analytics | onboarding | other)",
  "customer_tier": "string (free | pro | enterprise)",
  "customer_age_days": "integer (days as customer)",
  "is_repeat_issue": "boolean (same/similar issue in past 30 days)",
  "escalation_history": "array of {timestamp, reason, tier_assigned, resolved}",
  "knowledge_base_confidence": "number (0.0-1.0, from knowledge_retrieval)"
}
```

#### Outputs
```json
{
  "should_escalate": "boolean",
  "escalation_tier": "integer (null if should_escalate=false, else 1|2|3)",
  "reason": "string (primary reason for decision)",
  "secondary_reasons": "array of strings",
  "confidence": "number (0.0-1.0)",
  "recommended_agent_type": "string (enum: general | billing | integration_specialist | success_manager)",
  "suggested_priority_adjustment": "string (null | bump_up | maintain | defer)",
  "priority_justification": "string",
  "decision_made_by": "string (enum: rule_engine | llm_override)"
}
```

#### Triggers
- After sentiment analysis completes
- After knowledge_retrieval returns low confidence
- Every message when prior escalation exists
- Periodically for open conversations (re-evaluate every 15 min)

#### Decision Rules (Rule Engine)

```
IF sentiment_label == "angry":
  THEN escalate = TRUE, tier = 1, priority_bump = immediate
  
IF customer_request_explicit == "human_agent":
  THEN escalate = TRUE, tier = 2 (or 1 if sentiment=angry)
  
IF priority == "P1" OR priority == "P2":
  AND sla_breach_imminent == TRUE:
  THEN escalate = TRUE, tier = 1
  
IF failed_attempts >= 3:
  AND sentiment_label IN [frustrated, angry]:
  THEN escalate = TRUE, tier = 2, reason = "repeated failures"
  
IF issue_category == "integrations":
  AND sentiment_label IN [frustrated, angry]:
  THEN escalate = TRUE, tier = 2, recommended_agent_type = "integration_specialist"
  
IF issue_category == "billing":
  AND (sentiment_label IN [frustrated, angry] OR customer_request_explicit LIKE "refund"):
  THEN escalate = TRUE, tier = 1, recommended_agent_type = "billing"
  
IF is_repeat_issue == TRUE:
  AND failed_attempts >= 2:
  THEN escalate = TRUE, tier = 3, reason = "chronic issue"
  
IF knowledge_base_confidence < 0.55:
  AND failed_attempts >= 1:
  THEN escalate = TRUE, tier = 2, reason = "insufficient KB coverage"
  
IF customer_tier == "enterprise":
  AND priority IN [P1, P2]:
  THEN escalate = TRUE, tier = 1
```

#### LLM Override (Groq)
If no rule matches clearly, invoke LLM with context:
- "Given this customer's sentiment, priority, history, and category, should we escalate?"
- LLM votes on escalation + tier with reasoning
- Override allowed if confidence > 0.85

#### Tier Definitions
| Tier | SLA | Skill Level | Handled Categories |
|------|-----|-------------|-------------------|
| **1** | 15 min response | Senior CSM, urgent issues | Angry customers, refunds, P1, enterprise |
| **2** | 1 hour response | Specialist (billing/integration) | Failed attempts, category-specific issues, frustrated |
| **3** | 4 hour response | Product specialists | Chronic issues, custom config, investigations |

#### Monitoring
- Track: escalation rate by channel, tier distribution, accuracy of tier assignment
- Alert if: escalation rate > 40% (indicates system issues), tier 1 SLA missed

---

### Skill: `channel_adaptation`

**Version**: 1.0.0  
**Category**: Response Formatting  
**SLA**: <300ms response time

#### Description
Reformats and adapts agent response text according to target channel norms and constraints. Ensures email responses are formal with signatures, WhatsApp responses are brief with emoji, and web form responses are structured with CTAs.

#### Inputs
```json
{
  "raw_response": "string (agent-generated response in neutral format)",
  "channel": "string (enum: email | whatsapp | web)",
  "sentiment_context": "string (agent detected customer sentiment)",
  "conversation_history_length": "integer (number of prior messages)",
  "is_escalation": "boolean (true if handing off to human)",
  "agent_name": "string (display name for signature)",
  "customer_name": "string (optional)"
}
```

#### Outputs
```json
{
  "formatted_response": "string (ready to send)",
  "channel_used": "string",
  "formatting_applied": {
    "additions": "array of strings (greeting, signature, etc.)",
    "removals": "array of strings (overly formal phrases if WhatsApp, etc.)",
    "modifications": "array of {original, modified, reason}",
    "character_count": "integer",
    "line_count": "integer"
  },
  "compliance_checks": {
    "no_promises_made": "boolean",
    "no_pii_exposed": "boolean",
    "source_cited": "boolean",
    "escalation_option_offered": "boolean"
  },
  "quality_score": "number (0.0-1.0)"
}
```

#### Triggers
- After LLM generates response text (before sending)
- Manual override if quality_score < 0.75

#### Channel-Specific Rules

**Email Format**:
```
{greeting}

{response_body}

[If applicable: "Here are some helpful resources:"
{cited_sources_as_links}]

[If sentiment=frustrated: "I understand this is frustrating. How can I help further?"]

Best regards,
{agent_name}
Customer Success Team
[support contact info]
```
- Line length: soft wrap at 80 chars
- Formality: Match customer's formality level
- Closing: Always include sign-off + escalation offer if applicable

**WhatsApp Format**:
```
{greeting_optional, 1-5 words}

{response_body, max 2-3 sentences}

[emoji: ✅ 👍 😊 etc., ~20% of messages]

[CTA as direct link, no explanation]

[If escalation: "Want to chat with someone from our team? I'll connect you now 👋"]
```
- Line limit: Max 3 lines (can break into sequential messages)
- Tone: Conversational, avoid formal corporate speak
- Links: Short URLs only (bit.ly style)
- Emoji: Used at end of message or sentence for warmth

**Web Form Format**:
```
✅ {response_title}

{response_body, structured with headers if needed}

📚 Related Resources:
• [Link 1: Title]
• [Link 2: Title]

🎯 Next Steps:
1. Action 1
2. Action 2

[Button: "View Full Solution" | "Chat with Support" | "Done"]
```
- Structure: Use headers, bullet points, numbered lists
- CTAs: Clear action buttons, not just text links
- Visual hierarchy: Icons (✅ 🎯 📚) for scanning
- Escalation: "Chat with Support" button always visible

#### Compliance Checks
- **No Unauthorized Promises**: If response mentions refund/credit without ["approval_code", "APPROVED"], flag
- **No PII Exposure**: Mask customer emails, phone numbers in external communications
- **Source Citation**: If response based on KB, include link to source
- **Escalation Option**: If not escalating now, always offer "escalate if unhelpful"

#### Quality Scoring
| Factor | Weight | Criteria |
|--------|--------|----------|
| Relevance | 30% | Does response answer the question? |
| Tone Match | 25% | Does tone match customer/channel? |
| Clarity | 20% | Easy to understand? Jargon-free? |
| Completeness | 15% | All issues addressed? |
| Compliance | 10% | Passes all compliance checks? |

#### Monitoring
- Track: quality_score distribution, customer feedback on response clarity
- Alert if: quality_score < 0.70 for >10% of responses

---

### Skill: `customer_identification`

**Version**: 1.0.0  
**Category**: Data Lookup / Context  
**SLA**: <400ms response time

#### Description
Identifies customer in system from email, phone number, or name, retrieving account details, support history, customer tier, and open tickets. Provides agent with context for personalized responses and determines escalation tier eligibility.

#### Inputs
```json
{
  "email": "string (optional)",
  "phone": "string (optional, international format)",
  "name": "string (optional, customer provided name)",
  "conversation_thread_id": "string (optional, from channel)",
  "fuzzy_match_enabled": "boolean (default: true)",
  "include_sensitive_data": "boolean (default: false, restricts PII in logs)"
}
```

#### Outputs
```json
{
  "customer_found": "boolean",
  "customer_id": "string",
  "profile": {
    "name": "string",
    "email": "string (masked if include_sensitive=false)",
    "phone": "string (masked if include_sensitive=false)",
    "tier": "string (free | pro | enterprise)",
    "signup_date": "ISO8601",
    "days_as_customer": "integer",
    "account_status": "string (active | paused | churned | trial)"
  },
  "history_summary": {
    "total_tickets": "integer",
    "tickets_past_30_days": "integer",
    "avg_resolution_time": "string",
    "csat_score": "number (0-5, if available)",
    "open_ticket_ids": "array of strings",
    "repeat_issues": "array of {category, count, last_date}"
  },
  "risk_flags": {
    "is_vip": "boolean",
    "is_at_churn_risk": "boolean (based on engagement/CSAT)",
    "is_new_customer": "boolean (< 30 days)",
    "has_critical_open_issues": "boolean"
  },
  "confidence": "number (0.0-1.0)",
  "match_type": "string (enum: exact_email | exact_phone | fuzzy_name | no_match)"
}
```

#### Triggers
- On every inbound message (identify customer immediately)
- Escalation context building (retrieve full history for agent handoff)
- Customer explicitly states their identity or issue ID

#### Implementation Details
- **Tool Used**: `get_customer_history` (MCP tool connecting to CRM/database)
- **Fuzzy Matching**: Levenshtein distance on name, domain normalization on email
- **Data Privacy**: Mask email/phone in agent-facing UI if include_sensitive=false
- **Cache**: Recent lookups cached 5 min to reduce DB load

#### Confidence Interpretation
| Confidence | Match Type | Action |
|-----------|-----------|--------|
| >0.95 | Exact match | Full context available |
| 0.80-0.94 | Near-exact (email variant) | Verify with customer before using context |
| 0.60-0.79 | Fuzzy name match | Use with caution, confirm ID |
| <0.60 | No clear match | Treat as new customer, ask for verification |

#### Fallback (No Match)
If customer not found:
```json
{
  "customer_found": false,
  "suggested_action": "Ask for email or account ID to look up",
  "prompt_suggestion": "I'd like to help! Could you share your email or account ID so I can pull up your account?"
}
```

#### Monitoring
- Track: lookup success rate, average match confidence, false positive rate
- Alert if: lookup latency > 800ms (DB performance), match confidence < 0.65 for >5% of lookups

---

## Skill Orchestration

### Skill Execution Order (Typical Flow)
1. **customer_identification** → Get context
2. **sentiment_analysis** → Understand emotional state
3. **knowledge_retrieval** → Find relevant docs
4. **escalation_decision** → Decide if human needed
5. **channel_adaptation** → Format response

### Conditional Flows

**High-Confidence Self-Service Path** (Sentiment=Neutral, KB confidence >0.8):
1. sentiment_analysis
2. knowledge_retrieval
3. channel_adaptation
4. Send response

**Escalation Path** (Sentiment=Angry OR KB <0.6 OR Customer Request):
1. customer_identification
2. sentiment_analysis
3. escalation_decision
4. (Skip channel_adaptation, hand off to human)

**Complex Investigation Path** (Integration issues, repeat customer):
1. customer_identification
2. sentiment_analysis
3. knowledge_retrieval (with conversation history)
4. escalation_decision (likely tier 2-3)
5. Context bundle for human agent

---

## Skill Versioning & Updates

**Versioning Scheme**: MAJOR.MINOR.PATCH
- **MAJOR**: Breaking changes (e.g., new input required, different output structure)
- **MINOR**: New capability or improved accuracy (backward compatible)
- **PATCH**: Bug fixes (no behavioral change)

**Update Process**:
1. New version deployed alongside current version (A/B test if MAJOR)
2. Monitoring baseline established
3. Gradual rollout: 10% → 50% → 100% (over 48 hours)
4. Rollback plan: Automatic if error rate +5% or confidence -0.1

---

## Monitoring & SLOs

### Per-Skill Metrics
| Skill | SLO Latency | SLO Accuracy | Alert Threshold |
|-------|-------------|--------------|-----------------|
| knowledge_retrieval | <500ms | 94% | >600ms avg |
| sentiment_analysis | <200ms | 91% | >250ms avg |
| escalation_decision | <300ms | 92% | >400ms avg |
| channel_adaptation | <300ms | 95% | >400ms avg |
| customer_identification | <400ms | 98% | >600ms avg |

### Dashboards
- Real-time skill latency, error rates, confidence scores
- Per-channel performance (email vs WhatsApp vs web)
- Escalation funnel (funnel drop-off at each decision point)
- CSAT correlation with skill decisions

---

## Future Skill Extensions

- **feedback_loop**: Learn from corrections agents make
- **multi_turn_reasoning**: Maintain conversation state across multiple exchanges
- **proactive_outreach**: Identify at-risk customers and suggest help
- **competitor_analysis**: Understand competitive positioning (guardrailed)
- **custom_api_integration**: Flexible tool calling for customer-specific APIs

# NovaDeskAI Escalation Rules & Procedures

## Overview

Escalation is the process of routing customer issues to higher tiers of support when automated systems (NovaBot) cannot resolve them or when specific conditions warrant immediate human attention. Escalation rules are designed to ensure critical issues reach the right person quickly while allowing straightforward issues to be resolved efficiently by the bot.

---

## Escalation Trigger Conditions

### Automatic Escalation Triggers

The following conditions automatically escalate a ticket to Tier 2 (human agent):

#### 1. Sentiment-Based Escalation
- **Condition:** Customer sentiment detected as "angry" OR "very frustrated" + Priority P1
- **Action:** Immediate escalation to Tier 2
- **Notification:** Real-time Slack alert + email to assigned agent
- **Example:** Customer uses phrases like "unacceptable," "lawsuit," "criminal," combined with critical system failure

#### 2. Billing Disputes
- **Condition:** Issue tagged as "billing" AND dispute amount > $500 OR "refund requested" keyword detected
- **Action:** Automatic escalation to Tier 2 (Billing Specialist)
- **Escalation Note:** "High-value dispute - requires manual review and approval authority"
- **Example:** Customer disputes $1,200 charge and requests immediate refund

#### 3. Legal/Compliance Mentions
- **Condition:** Keywords detected: "lawyer," "lawsuit," "GDPR," "HIPAA," "breach," "compliance," "legal action"
- **Action:** Immediate escalation to Tier 3 (Senior Manager/Legal)
- **Notification:** Slack ping to #legal-compliance channel + email to manager
- **Hold:** Do not respond until Tier 3 reviews (auto-responder: "We're investigating this matter carefully")
- **Example:** Customer mentions potential legal action or regulatory violation

#### 4. Failed Resolution Attempts
- **Condition:** Ticket has 3+ failed resolution attempts from NovaBot OR agent attempted solution 3+ times with customer rejection
- **Action:** Escalate to Tier 2 with different agent OR escalate to Tier 3 if still unresolved
- **Escalation Note:** Include summary of all attempted solutions and why they failed
- **Example:** Customer says "I tried that already, it didn't work" three times

#### 5. Customer Requests Human Agent
- **Condition:** Customer explicitly states "I need a human," "I want to speak to someone," "transfer me to a person," OR uses escalation keywords: "manager," "supervisor," "support team"
- **Action:** Immediate escalation to Tier 2 (next available agent)
- **Response Time:** Maximum 5 minutes for connection
- **Example:** "Can I please talk to a real person?" or "I need to speak with a manager"

#### 6. SLA Window Breach Risk
- **Condition:** Ticket approaching SLA deadline without resolution:
  - P1: < 15 minutes remaining to 4-hour resolution SLA
  - P2: < 1 hour remaining to 24-hour resolution SLA
  - P3: < 4 hours remaining to 72-hour resolution SLA
- **Action:** Auto-escalate to Tier 2 OR Tier 3 depending on priority
- **Notification:** "SLA at risk" alert in Slack
- **Example:** P1 ticket open for 3h 50m with no resolution in sight

#### 7. Data Loss or Security Incident
- **Condition:** Keywords: "data loss," "deleted," "missing," "hacked," "security," "breach," "unauthorized access"
- **Action:** Immediate escalation to Tier 3 (Manager) + Tech Lead
- **Notification:** Critical alert in #security-incidents channel
- **Hold:** No customer response until severity verified
- **Example:** "All my customer data disappeared from our account"

#### 8. System Outage Report
- **Condition:** Multiple P1 tickets reporting same system issue OR "system down," "cannot access," "503 error," "outage"
- **Action:** Immediate escalation to Tier 3 (Engineering Manager)
- **Notification:** #critical-incidents channel + all hands Slack notification
- **Parallel Action:** Create incident ticket in engineering system
- **Example:** 5+ customers reporting inability to log in

#### 9. Unresolved After Maximum Time
- **Condition:** Ticket open > SLA window elapsed without resolution + still requires work
- **Action:** Escalate to Tier 3 (Senior Manager) for review
- **Review Required:** Why wasn't this resolved? What's blocking closure?
- **Example:** P2 ticket open for 48+ hours

---

## Escalation Tiers

### Tier 1: NovaBot (Automated AI)
**Role:** Provide immediate, automated responses  
**Capabilities:**
- Answer FAQ and common questions
- Provide documentation links
- Collect customer information
- Suggest solutions from knowledge base
- Route to appropriate Tier 2 agent

**Escalation Authority:** Cannot approve refunds, cannot override policies, cannot make business decisions

**Success Rate Target:** 35-50% of issues deflected (not requiring human escalation)

### Tier 2: Human Agent (Support Team Member)
**Role:** Resolve customer issues directly  
**Qualifications:**
- Minimum 3 months product knowledge
- Trained on company policies and procedures
- Access to customer account history
- Can make certain decisions within authority limits

**Decision Authority:**
- Approve refunds up to $100
- Extend trial periods
- Grant feature access for testing
- Adjust billing/payment issues
- Grant account credit up to $50

**Escalation Criteria:** Cannot resolve, requires policy exception, customer demands manager

**SLA:** Respond within 4 hours for P2, take ownership of ticket

**Success Rate Target:** Resolve 70%+ of escalated issues without further escalation

### Tier 3: Senior Agent / Manager (Support Manager or Senior Support Agent)
**Role:** Handle complex issues, make business decisions, manage escalations  
**Qualifications:**
- Minimum 1 year in support role
- Deep product knowledge
- Management/leadership training
- Empowered to make business decisions

**Decision Authority:**
- Approve refunds $100-$1,000
- Override normal policies (with justification)
- Grant feature access/special accommodations
- Terminate customer relationships (with approval)
- Make commitments about future product roadmap (limited)
- Legal review authority
- Customer retention decisions

**Escalation Criteria:** Tier 2 cannot resolve, legal/compliance issue, VIP customer, very angry customer

**Response Time:** Respond within 1 hour for P1, 2 hours for P2

**Success Rate Target:** Resolve 95%+ of escalated issues without further escalation

### Tier 4: Executive (VP Customer Success or Head of Support)
**Role:** Crisis management, PR issues, strategic decisions  
**Activation:** Only for extreme cases (lawsuit threat, major PR risk, significant customer relationship at risk)

**Decision Authority:**
- Unlimited refunds with justification
- Major policy exceptions
- PR/comms coordination
- Customer retention at any level
- VIP customer issues

---

## Escalation Workflow & Process

### Escalation Path A: Bot → Tier 2 (Most Common)

```
1. NovaBot detects escalation trigger
   ↓
2. Bot prepares escalation package:
   - Full conversation history
   - AI-generated summary of issue
   - Recommended next steps
   - Customer sentiment analysis
   - Relevant account information
   ↓
3. Bot sends to Tier 2 queue with:
   - Ticket priority updated if needed
   - Auto-assign to next available agent
   OR hold in "Escalated" queue for manual assignment
   ↓
4. Tier 2 agent receives notification:
   - Slack message (for P1: @channel, for P2: channel mention)
   - Email notification
   - Ticket marked with "Escalated from Bot" tag
   ↓
5. Tier 2 agent takes ownership:
   - Reviews bot's escalation summary
   - Reviews full customer history
   - Makes decision: resolve or escalate further
```

### Escalation Path B: Tier 2 → Tier 3

```
1. Tier 2 agent determines issue needs escalation
   ↓
2. Agent marks ticket as "Escalation to Manager"
   ↓
3. Agent adds escalation note:
   - Why Tier 2 cannot resolve
   - What was tried
   - Recommended action
   - Decision authority needed
   ↓
4. Tier 3 manager notified:
   - Slack direct message
   - Email with full context
   ↓
5. Tier 3 takes ownership:
   - Makes decision/business judgment
   - Updates customer
   - Resolves or creates follow-up tasks
```

### Escalation Path C: Direct Tier 3 (High-Severity Issues)

Certain issue types skip Tier 2 and go directly to Tier 3:

- **Security breaches** → Tier 3 + Tech Lead
- **Legal threats** → Tier 3 + Legal
- **System outages** → Tier 3 + Engineering Manager
- **Major billing disputes** ($5,000+) → Tier 3 + Finance
- **VIP customer issues** → Dedicated account manager (Tier 3+)

---

## Auto-Escalation vs. Manual Escalation

### Auto-Escalation (Triggered Automatically by System)

**When It Happens:**
- Bot detects escalation trigger condition
- System automatically moves ticket to escalation queue
- No human action required to initiate

**Conditions:**
- Sentiment = "angry" + P1
- Keywords detected (lawyer, GDPR, etc.)
- SLA at risk threshold reached
- Escalation threshold exceeded

**Advantages:**
- Instant response to critical issues
- No risk of human forgetting
- Consistent application of rules
- 24/5 coverage (even outside business hours)

**Process:**
- System flags ticket
- Auto-adds escalation tags
- Moves to Tier 2 queue
- Sends notifications

### Manual Escalation (Agent Initiated)

**When It Happens:**
- Tier 1 (NovaBot) or Tier 2 agent clicks "Escalate" button
- Agent determines escalation is needed but didn't auto-trigger

**Conditions:**
- Complex issue requiring judgment call
- Customer requests escalation
- Needs second opinion from senior agent
- Special circumstances requiring manager

**Process:**
1. Agent clicks "Escalate to Manager" in ticket UI
2. Agent adds escalation reason/notes
3. Agent selects priority level
4. System routes to manager queue
5. Manager receives notification and takes next action

---

## Notification Rules

### Slack Alerts

**P1 Escalations:**
- Message to: `#critical-support` channel + `@support-manager`
- Format: "🚨 CRITICAL P1 ESCALATION: [Customer] - [Issue Summary]"
- Include: Link to ticket, quick action buttons
- Repeat notification every 15 minutes if unacknowledged

**P2 Escalations:**
- Message to: `#escalations` channel (no auto-mention)
- Format: "⚠️ P2 Escalation: [Customer] - [Issue]"
- Include: Ticket link, customer context
- Notification sent once

**P3 Escalations:**
- Email only (no Slack, to reduce noise)
- Digest sent once per hour

**High-Severity Issues (Legal, Security, Data Loss):**
- `#critical-incidents` channel with all hands notification
- Direct Slack message to VP Customer Success
- SMS alert (high-severity only)

### Email Alerts

**Recipients:**
- Assigned agent (always for Tier 2 escalations)
- Manager (for Tier 3 escalations)
- Relevant department heads (for legal/security issues)

**Content:**
- Ticket ID and customer name
- Issue summary
- Why escalated
- Recommended next steps
- Link to ticket

**Response Time Expectations:**
- P1: Acknowledge within 5 minutes, respond within 1 hour
- P2: Acknowledge within 15 minutes, respond within 4 hours
- P3: Acknowledge within 1 hour, respond within 24 hours

---

## SLA Breach Escalation Matrix

| Priority | SLA Window | Escalation Trigger | Action |
|----------|-----------|-------------------|--------|
| P1 | 4 hours | < 15 min remaining | Escalate to Tier 3 immediately |
| P1 | 4 hours | Already breached | Tier 3 + Manager notification + customer apology |
| P2 | 24 hours | < 1 hour remaining | Escalate to Tier 2 (bump priority) |
| P2 | 24 hours | Already breached | Escalate to Tier 3 + customer notification |
| P3 | 72 hours | < 4 hours remaining | Escalate to Tier 2 (flag for attention) |
| P3 | 72 hours | Already breached | Flag for review (no auto-escalation) |

**SLA Breach Recovery:**
1. Immediate escalation to manager
2. Manager makes priority decision on resolution
3. Customer sent apology note + brief explanation
4. Discount or credit offered (Tier 3 decision): $25-$100 depending on severity
5. Post-mortem analysis: Why did SLA breach happen?
6. Prevention plan: What systems/processes need improvement?

---

## De-Escalation Criteria

When a ticket has been escalated, it can be de-escalated back to Tier 2 or closed if:

### Tier 3 → Tier 2 De-escalation Conditions:

✓ Issue resolved and customer satisfied (CSAT collected)  
✓ Customer explicitly says issue is resolved  
✓ Follow-up work is routine/straightforward  
✓ No further business judgment needed  
✓ No risk of recurrence  

**Process:**
1. Tier 3 adds de-escalation note
2. Reassigns to specific Tier 2 agent if follow-up needed
3. Removes "escalated" tag
4. Closes ticket if fully resolved

### Tier 2 → Closed De-escalation Conditions:

✓ Customer confirmed issue is fixed  
✓ All attempted solutions exhausted OR solution applied successfully  
✓ Customer satisfied or explicitly accepts resolution  
✓ No further action required  

**Process:**
1. Agent sends final response with confirmation
2. Agent marks ticket status as "Resolved"
3. Auto-send CSAT survey
4. Ticket auto-closes after 3 days if no customer response

---

## Do-Not-Escalate Conditions

These issues should NOT be escalated, even if they seem urgent:

### ❌ Do NOT Escalate:

1. **Feature Requests** (unless from major customer)
   - Route to product team instead
   - Customer should understand this is feedback, not urgent

2. **Spam or Inappropriate Content**
   - Delete and block sender
   - Do not waste agent time

3. **Duplicate Tickets** (same customer, same issue)
   - Merge into original ticket
   - Add comment with update
   - Close duplicate

4. **Out-of-Scope Issues**
   - Example: "Can you help me with my laptop?"
   - Politely decline and suggest appropriate resource
   - Close ticket

5. **P3 Issues After Hours** (unless P3 becomes P2/P1)
   - Route to next business day
   - Send auto-response: "We'll get back to you tomorrow during business hours"
   - Note: P1/P2 issues are always escalated immediately regardless of time

6. **Vague/Incomplete Tickets**
   - Bot should ask clarifying questions first
   - Example: "Help!" with no details
   - Request more information before escalating
   - Max 2 clarification attempts before escalating

7. **Password Resets** (if self-service available)
   - Should be auto-handled by bot
   - Only escalate if customer doesn't receive reset email

---

## Special Escalation Rules

### VIP Customers

**Definition:** Customers on Scale plan + $5,000+/month ARR, or strategic partners

**Escalation Treatment:**
- Dedicated account manager assigned
- All issues escalate to Tier 3 immediately
- Response time: 1 hour maximum
- Issue gets priority in queue
- Manager provides direct contact information

**Escalation Note:** Include "VIP CUSTOMER" tag

### Repeat Issues

**Definition:** Same issue escalated 2+ times by same customer within 30 days

**Action:**
- Escalate to Tier 3 for root cause analysis
- Escalation note: "REPEAT ISSUE - investigate system/process failure"
- Engineer assessment: Is this a product bug or customer error?
- If product bug: Create incident for engineering team
- If customer error: Create training plan or knowledge base article

### Competitive Intelligence

**Definition:** Customer mentions switching to competitor, considering cancellation

**Action:**
- Escalate to Tier 3 (Account Manager/VP)
- Flag as "Retention Risk"
- Manager initiates retention conversation within 4 hours
- Special attention to customer concerns
- Possible discount/concession offered

**Note:** Never dismiss customer if they express interest in competitor

### Bulk Escalations

**Definition:** Same issue escalated by 5+ customers within 24 hours

**Action:**
- Alert: Create system status incident ticket
- Escalate to Engineering Manager
- Post status update to all affected customers
- Public status page notification
- Coordinate response communications

---

## Escalation Quality Standards

### Success Metrics for Escalations:

- **Resolution on First Escalation:** 80%+ of escalated tickets resolved without further escalation
- **Customer Satisfaction:** CSAT 4.5+ on escalated issues (higher satisfaction expected after escalation)
- **Time to Resolution:** 90% of escalations resolved within SLA window
- **Manager Response Time:** 95% of escalations acknowledged by manager within specified time
- **Escalation Appropriateness:** 90%+ of escalations meet defined escalation criteria

### Escalation Audit

**Monthly Review:**
- Sample 20 escalated tickets
- Verify escalation was appropriate
- Check if rules were followed correctly
- Assess quality of Tier 2/3 resolutions
- Identify training gaps or rule improvements

**Metrics Dashboard:**
- Escalation rate by cause
- Average time to escalation
- Average time to resolution after escalation
- Escalation volume by agent (identify patterns)
- De-escalation rate

---

## Escalation Communication Templates

### Bot to Customer (Escalating):
```
"Thanks for your patience. This issue needs a closer look from our support team. 
I'm connecting you with [Agent Name] who specializes in [issue area]. 
They'll reach out within [SLA time] with a solution. We appreciate your patience!"
```

### Tier 2 to Tier 3 (Escalation Note):
```
"Escalating for manager review. Customer is very frustrated about [issue]. 
I've attempted [solutions tried]. Customer is considering cancellation. 
Needs Tier 3 decision authority on [specific decision needed]. Customer is on Scale plan."
```

### Manager to Customer (High-Severity):
```
"I'm [Manager Name], the support manager on your case. I understand this is urgent 
and I want to personally ensure we resolve this quickly. Here's what I'm doing right now: 
[specific next steps]. I'll follow up with you by [time]."
```

---

**Last Updated:** February 2026  
**Next Review:** May 2026

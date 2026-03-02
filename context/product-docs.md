# NovaDeskAI Product Documentation

## Table of Contents
1. [Getting Started](#getting-started)
2. [NovaBot Configuration](#novabot-configuration)
3. [NovaDeskAI Platform Features](#novadesk-platform-features)
4. [NovaSight Analytics](#novasight-analytics)
5. [Integrations](#integrations)
6. [Billing & Subscriptions](#billing--subscriptions)
7. [Troubleshooting](#troubleshooting)
8. [FAQ](#faq)

---

## Getting Started

### Onboarding Overview
Welcome to NovaDeskAI! This section guides you through the initial setup to get your support operation running.

### Step 1: Account Creation & Setup (15 minutes)
1. Sign up at https://app.novadesk.ai/signup
2. Verify your email address
3. Create your workspace and set timezone preferences
4. Add your team members (email invitations sent automatically)
5. Complete your company profile information

### Step 2: Knowledge Base Creation (30-45 minutes)
1. Navigate to **Settings > Knowledge Base**
2. Create categories for your products/services
3. Upload FAQ articles, help docs, or paste content
4. Enable automatic indexing for NovaBot training
5. Test the search functionality

### Step 3: Channel Configuration (varies)
- **Email:** Connect via OAuth or SMTP forwarding
- **WhatsApp:** Use WhatsApp Business API credentials
- **Web Form:** Get embed code and add to your website

### Step 4: NovaBot Training (1-2 hours)
1. Configure bot personality and tone
2. Define escalation triggers
3. Create custom response templates
4. Set up conversation flow rules
5. Run test conversations

### Step 5: Team Onboarding (varies)
1. Set user roles: Admin, Senior Agent, Agent, Viewer
2. Create assignment rules (round-robin, skill-based, etc.)
3. Set up agent availability schedules
4. Configure notification preferences

---

## NovaBot Configuration

### Channel Settings

#### Email Configuration
- **Provider:** Gmail API, Microsoft 365, or custom SMTP
- **Response Format:** Plain text, HTML, or Markdown
- **Signature:** Auto-append company signature to all responses
- **Rate Limiting:** Configure max emails per minute to prevent throttling
- **Auto-Reply:** Set vacation/out-of-office messages

#### WhatsApp Configuration
- **API Credentials:** Obtain from WhatsApp Business dashboard
- **Message Templates:** Pre-approve message templates with WhatsApp
- **Media Support:** Enable/disable image and document sharing
- **Session Management:** Configure session timeout (default: 24 hours)
- **Quick Replies:** Set common response buttons

#### Web Form Configuration
- **Embed Location:** Website pages or help center
- **Custom Branding:** Match company colors and logo
- **Form Fields:** Customize required and optional fields
- **Pre-fill:** Auto-populate user info if logged in
- **Redirect:** Send confirmed submissions to thank-you page

### Tone & Personality Settings

**Tone Slider (1-10 Scale):**
- 1-3: Formal/Professional (enterprise tone)
- 4-6: Balanced/Friendly (most common)
- 7-9: Casual/Conversational (startup tone)
- 10: Fun/Playful (brand personality)

**Personality Options:**
- Technical Expert (detailed, precise)
- Friendly Assistant (warm, approachable)
- Problem Solver (action-oriented, solution-focused)
- Brand Ambassador (brand-aware, marketing-conscious)

**Language & Grammar:**
- Use contractions (e.g., "I'll" instead of "I will")
- Avoid jargon when possible
- Use active voice
- Keep sentences under 20 words average

### Escalation Thresholds

Configure when NovaBot should escalate to human agents:

```
Automatic Escalation Triggers:
- Sentiment detected as "angry" or "very frustrated"
- Customer explicitly requests human agent
- Bot confidence < [threshold]% (configurable: 40-70%)
- Issue category: "billing" or "account" (configurable)
- Conversation turns > [threshold] (configurable: 5-15)
- Unresolved after 2 resolution attempts
- Keywords detected: refund, cancel, complaint, lawyer
```

**Escalation Handling:**
1. Notify agent in real-time via Slack/Email
2. Transfer full conversation history
3. Display pre-drafted summary to agent
4. Set priority based on original ticket priority
5. Include bot's attempted resolutions in context

### Response Templates & Canned Responses

**Template Categories:**
- Greeting messages
- Acknowledgment responses
- Troubleshooting guides
- Billing inquiries
- Feature requests
- Escalation handoff

**Template Features:**
- Variable placeholders: {{customer_name}}, {{company}}, {{issue_id}}
- Conditional logic: if/else blocks for dynamic content
- Action suggestions: auto-suggest next steps
- A/B testing: measure effectiveness of different responses

**Example Template:**
```
Hi {{customer_name}},

Thanks for reaching out about {{issue_category}}. I understand how frustrating this must be.

[CONDITIONAL: if billing_issue]
I'd like to help resolve your billing concern right away. Can you share:
1. Your invoice number
2. The discrepancy you noticed
3. Your preferred resolution

[CONDITIONAL: if technical_issue]
Let's troubleshoot this together. First, could you try:
1. {{troubleshooting_step_1}}
2. {{troubleshooting_step_2}}

Please let me know if that resolves it!

Best regards,
Nova
```

---

## NovaDeskAI Platform Features

### Ticket Management

**Ticket Lifecycle:**
1. **Creation:** Incoming from Email, WhatsApp, or Web form
2. **Routing:** Automatic assignment based on skills/availability
3. **Resolution:** Agent interaction with full history
4. **Closure:** Customer satisfaction confirmation
5. **Archival:** 90-day retention, then archive

**Ticket Views:**
- **Inbox:** All unassigned tickets
- **My Queue:** Assigned to current user
- **All Tickets:** Full search and filter
- **Escalated:** High-priority escalations
- **Resolved:** Closed tickets (searchable)

**Ticket Properties:**
- Ticket ID (auto-generated: TKT-XXXXX)
- Customer info (name, email, company)
- Channel (email, whatsapp, web)
- Priority (P1, P2, P3)
- Status (open, in_progress, resolved, escalated)
- Created/Updated/Resolved timestamps
- Assigned agent
- Tags (auto-populated or manual)
- Related tickets (link duplicates/related issues)

**Batch Actions:**
- Bulk reassign tickets
- Bulk priority change
- Bulk tag application
- Bulk status update
- Export to CSV

### Auto-Tagging System

**How It Works:**
1. Each incoming ticket is automatically analyzed
2. AI identifies relevant tags from knowledge base and trained categories
3. Confidence scores displayed (user can accept/reject)
4. Custom rules allow override and priority tags

**Predefined Tag Categories:**
- **Product:** Platform, NovaBot, NovaSight
- **Issue Type:** Bug, Feature Request, Integration, Billing, Account, General
- **Urgency:** Critical, High, Medium, Low
- **Status:** Waiting for Customer, Waiting for Engineering, In Progress
- **Resolution:** Documented, Training, Escalation Needed

**Custom Tags:**
Create unlimited custom tags for your specific use cases.

### SLA Tracking

**Real-Time Monitoring:**
- Dashboard shows % tickets within SLA for each priority
- Visual indicators: Green (on track), Yellow (at risk), Red (breached)
- Historical trending with monthly reports
- Per-agent SLA compliance metrics

**SLA Definitions:**
```
Priority P1: First Response < 1 hour, Resolution < 4 hours
Priority P2: First Response < 4 hours, Resolution < 24 hours
Priority P3: First Response < 24 hours, Resolution < 72 hours
```

**SLA Breach Handling:**
1. Automatic priority escalation
2. Manager notification via Slack
3. Ticket highlighted in queue
4. Retry escalation every 15 minutes
5. Post-mortem analysis available after closure

### Canned Responses Library

**Organization:**
- Organize by category, product, issue type
- Search by keyword
- Mark as favorites for quick access
- Version control with approval workflow

**Smart Suggestions:**
- NovaBot suggests relevant canned responses based on ticket content
- Agent can edit before sending
- Feedback loop improves suggestions over time

**Response Analytics:**
- Usage frequency
- Customer satisfaction when used
- Effectiveness metrics
- Recommendations to retire or improve responses

---

## NovaSight Analytics

### Key Metrics

**CSAT (Customer Satisfaction Score)**
- Scale: 1-5 (displayed as 1-5 stars)
- Collected post-resolution via email survey
- Monthly average tracked
- Breakdown by agent, channel, issue type
- Target: 4.5+ average

**FRT (First Response Time)**
- Time from ticket creation to first agent response
- Measured in minutes
- Tracked by channel and agent
- Target: Align with SLA commitments

**AHT (Average Handle Time)**
- Total time from ticket open to resolution
- Includes all interactions (email threads, chat exchanges)
- Breakdown by priority and issue type
- Target: Reduce by 15-20% via process improvements

**Deflection Rate**
- % of issues resolved by NovaBot without escalation
- Key efficiency metric
- Target: 35-50% depending on industry
- Identifies improvement areas for bot training

**Resolution Rate**
- % of tickets resolved on first contact (FCR)
- Tracked by agent and team
- Higher = better customer experience
- Target: 60%+

**NPS (Net Promoter Score)**
- Quarterly survey: "How likely to recommend?"
- Calculated from customer responses
- Goal: Industry-leading 67+
- Segment by customer segment/product

### Dashboard Setup

**Default Dashboard Widgets:**
1. Today's metrics (CSAT, FRT, tickets handled)
2. This week's trends (line charts)
3. Team performance leaderboard
4. Open ticket queue status
5. SLA compliance at a glance
6. Bot deflection rate
7. Channel breakdown (email/whatsapp/web)
8. Sentiment distribution

**Custom Dashboards:**
- Save multiple dashboard configurations
- Share with team members
- Schedule automated reports (daily/weekly/monthly)
- Export as PDF or email

**Real-Time Alerts:**
- SLA breach alerts
- High sentiment escalations
- Bot confidence drops
- Agent availability warnings

### Report Builder

**Pre-Built Reports:**
- Daily standup report
- Weekly team performance
- Monthly customer satisfaction trends
- Quarterly business review
- Annual performance summary

**Custom Report Fields:**
- Time period: today, this week, custom range
- Metrics: Any combination of available metrics
- Filters: By agent, channel, priority, tags
- Grouping: By day, week, month, agent, channel

---

## Integrations

### Gmail API Integration

**Setup:**
1. Go to **Settings > Integrations > Gmail**
2. Click "Connect Gmail Account"
3. Authenticate with Google (OAuth 2.0)
4. Select label for support emails
5. Test connection

**Features:**
- Auto-sync incoming emails to tickets
- Send responses directly from NovaDeskAI
- Preserve threading and context
- Multi-account support

**Troubleshooting:**
- Verify OAuth permissions granted
- Check Gmail label configuration
- Ensure "Less secure app access" enabled (if needed)
- Verify API quota not exceeded

### WhatsApp Cloud API Integration

**Setup:**
1. Register WhatsApp Business Account
2. Generate API credentials from Meta Business dashboard
3. In NovaDeskAI: **Settings > Integrations > WhatsApp**
4. Paste API credentials
5. Approve message templates
6. Test with WhatsApp Business Account

**Features:**
- Inbound message routing to tickets
- Media message support (images, documents)
- Template message sending (for bulk notifications)
- Webhook for real-time updates

**Constraints:**
- Templates must be pre-approved by WhatsApp
- 24-hour message window after customer initiates
- Rate limits apply (100 msg/sec per account)

### Slack Integration

**Setup:**
1. **Settings > Integrations > Slack**
2. Click "Connect to Slack"
3. Authorize NovaDeskAI app in Slack workspace
4. Choose notification channel(s)
5. Configure alert types

**Notifications:**
- New P1 tickets (real-time)
- New P2 tickets (real-time)
- Escalations (real-time)
- SLA breaches (real-time)
- Daily summary (morning standup)
- Weekly metrics digest

**Slash Commands:**
- `/novabot status` - Get current metrics
- `/novabot queue` - See open tickets
- `/novabot assign @user` - Assign from Slack

### Zapier Integration

**Supported Triggers:**
- New ticket created
- Ticket status changed
- Ticket escalated
- SLA breached
- High sentiment detected

**Supported Actions:**
- Create Jira issue
- Send to Google Sheets
- Create Asana task
- Post to Slack (advanced)
- Send email via SendGrid
- Create Salesforce lead/opportunity

**Example Workflows:**
```
Trigger: Ticket created with tag "Feature Request"
Action: Create Asana task in "Product Ideas" board

Trigger: Ticket escalated to P1
Action: Create Jira issue in "Urgent" project and notify team in Slack
```

### REST API

**Base URL:** `https://api.novadesk.ai/v1/`

**Authentication:**
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" https://api.novadesk.ai/v1/tickets
```

**Key Endpoints:**
- `GET /tickets` - List all tickets
- `POST /tickets` - Create new ticket
- `GET /tickets/{id}` - Get ticket details
- `PATCH /tickets/{id}` - Update ticket
- `POST /tickets/{id}/comments` - Add comment
- `GET /knowledge-base` - Search KB
- `GET /analytics/metrics` - Get metrics
- `POST /webhooks` - Configure webhooks

**Rate Limits:**
- Standard tier: 1,000 requests/hour
- Pro tier: 10,000 requests/hour
- Enterprise: unlimited

**Webhook Events:**
- `ticket.created`
- `ticket.updated`
- `ticket.resolved`
- `ticket.escalated`
- `comment.added`
- `bot.escalated`

---

## Billing & Subscriptions

### Pricing Tiers

#### Starter Plan - $49/month
**Best for:** Small teams, single product support

- Up to 5 team members
- Up to 100 tickets/month
- 2 channels (email + one other)
- Basic NovaBot (templated responses)
- Standard SLA support (P3 only)
- 7-day data retention
- Email & community support

#### Growth Plan - $149/month
**Best for:** Growing SaaS companies, 10-50 employees

- Up to 20 team members
- Up to 1,000 tickets/month
- All 3 channels (email, WhatsApp, web)
- Advanced NovaBot (custom training)
- Standard SLA support (P2 & P3)
- 30-day data retention
- Integrations: Gmail, Slack, Zapier, REST API
- Priority email support + Slack channel
- NovaSight analytics (basic)

#### Scale Plan - $499/month
**Best for:** Established companies, 100+ employees

- Unlimited team members
- Unlimited tickets
- All 3 channels + custom channels
- Enterprise NovaBot (advanced AI, custom models)
- Premium SLA support (P1, P2, P3)
- 90-day data retention + archival
- All integrations + custom API support
- Dedicated account manager
- Priority Slack + phone support (24/5)
- Advanced NovaSight analytics & BI exports
- SSO/SAML authentication
- Custom SLAs
- Compliance: SOC 2, HIPAA, GDPR

### Billing Details

**Billing Cycle:** Monthly, charged on same day each month

**Payment Methods:**
- Credit/Debit card (Visa, Mastercard, Amex)
- Bank transfer (ACH for Scale customers)
- Invoice billing (for customers with $500+/month)

**Usage-Based Add-ons:**
- Extra team member: $10/user/month
- Extra 1,000 tickets/month: $5 (Starter/Growth only)
- Custom integrations: $50/month per integration
- Dedicated support: $200/month

**Discounts:**
- Annual commitment: 15% off
- Non-profit: 40% off
- Startup program: 50% off (first year)

**Refund Policy:**
- 30-day money-back guarantee on annual plans
- Prorated refunds for mid-cycle cancellation
- No refund within 7 days of next renewal

### Subscription Management

**In-App Controls:**
- Upgrade/downgrade plan (effective next cycle)
- Pause subscription (up to 30 days)
- Add/remove team members
- Update payment method
- Download invoices
- Export data before cancellation

---

## Troubleshooting

### Login Issues

**Problem:** Can't log in to account
**Solutions:**
1. Verify email address is correct
2. Click "Forgot Password?" and reset
3. Check email spam folder for reset link
4. Try incognito browser window
5. Clear browser cookies and cache
6. If using SSO, verify with IT team

**Escalation:** Contact support@novadesk.ai with your email

### Webhook Setup Issues

**Problem:** Webhooks not firing
**Debug Steps:**
1. Verify webhook endpoint returns HTTP 200
2. Check webhook URL is publicly accessible (no localhost)
3. Verify authentication headers if required
4. Check request body format matches documentation
5. Review webhook logs in **Settings > Webhooks > Recent Deliveries**
6. Test webhook manually: copy example JSON and send POST request

**Common Issues:**
- Endpoint returning 4xx/5xx errors
- Network firewall blocking outbound requests
- Request timeout > 30 seconds
- Incorrect API key in authentication header

### API Key Rotation

**Steps:**
1. Go to **Settings > API Keys**
2. Click "Generate New Key"
3. New key becomes active immediately
4. Old key remains valid for 7 days (grace period)
5. Update all integrations to use new key
6. After all updated, click "Revoke" on old key

**Best Practices:**
- Rotate keys every 90 days
- Revoke immediately if compromised
- Use separate keys per integration
- Store keys in secure vault (not code)

### Bot Not Responding

**Troubleshooting:**
1. Verify bot is enabled: **Settings > NovaBot > Status: Enabled**
2. Check escalation threshold not set too low
3. Verify knowledge base has relevant content
4. Confirm customer message matched expected channel
5. Review bot logs in **Analytics > Bot Logs**
6. Test with sample message in sandbox mode

**Common Causes:**
- Knowledge base empty or not trained
- Escalation configured to trigger on all messages
- Bot confidence threshold too high
- API rate limits exceeded
- Integration not connected properly

### Integration Connection Issues

**Gmail:**
- Verify OAuth token not expired
- Check Gmail label exists
- Ensure API quota available

**WhatsApp:**
- Verify API credentials correct
- Check business account verified
- Ensure phone number confirmed

**Slack:**
- Verify app installed in workspace
- Check bot has channel permissions
- Confirm webhook not revoked

---

## FAQ

### General Questions

**Q: How long does setup take?**
A: Basic setup (channels + bot) takes 1-2 hours. Full training and optimization takes 1-2 weeks.

**Q: Can I import existing tickets?**
A: Yes! Use our data import tool or REST API. We support CSV, JSON, or direct API calls. Bulk imports processed within 24 hours.

**Q: What languages does NovaDeskAI support?**
A: Currently English, Spanish, French, German, and Japanese. Additional languages coming in Q3 2026.

**Q: How do I cancel my subscription?**
A: Go to **Settings > Billing > Cancel Subscription**. Prorated refunds issued if within billing period.

### Technical Questions

**Q: Is my data encrypted?**
A: Yes! End-to-end encryption for all data in transit and at rest. AES-256 encryption standard.

**Q: What's your uptime SLA?**
A: 99.95% uptime guarantee. We maintain redundant infrastructure across multiple regions.

**Q: How do I export my data?**
A: Go to **Settings > Data Export**. Export as JSON, CSV, or database backup.

**Q: Can I use custom domains?**
A: Yes, on Growth and Scale plans. Set up CNAME records to route mail to NovaDeskAI infrastructure.

### Product Questions

**Q: Can NovaBot handle complex multi-step processes?**
A: Yes! Build conversation flows with branching logic, escalation conditions, and data collection forms.

**Q: How accurate is auto-tagging?**
A: 92%+ accuracy on predefined categories. Improves over time with human feedback.

**Q: What's included in "unlimited tickets"?**
A: All incoming and outgoing messages across all channels. No hidden limits.

**Q: How do I measure ROI from NovaDeskAI?**
A: Track deflection rate (bot resolution %), reduction in AHT, and CSAT improvement. Most customers see 3-6 month payback period.

**Q: Do you offer training for my team?**
A: Yes! Free onboarding calls, video courses, and documentation. Scale plan includes monthly training sessions.

**Q: Can I create custom reports?**
A: Absolutely. Our report builder is flexible with no limits on custom metrics or filters.

---

**Last Updated:** February 2026  
**Next Review:** May 2026

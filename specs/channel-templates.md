# Channel-Specific Response Templates

**Project:** NovaDeskAI Customer Success Agent  
**Stage:** 1 - Prototype & Discovery  
**Date:** 2026-02-27  
**Document Version:** 1.0

---

## Overview

This document contains channel-specific response templates discovered and validated during Stage 1 testing. Templates are organized by:
1. **Structure templates** (greeting, body, CTA, sign-off)
2. **Issue-type templates** (6 issue types × 3 channels = 18 templates)
3. **Response length guidelines**

All templates use `{placeholders}` for dynamic content. Tone and formatting are calibrated for each channel.

---

## Response Length Guidelines

| Metric | Email | WhatsApp | Web |
|--------|-------|----------|-----|
| **Greeting** | 1 line (5-10 words) | None | 1 line (3-5 words) |
| **Body** | 3-5 sentences (100-250 words) | 1-2 sentences (30-100 chars) | 2-3 sentences (50-150 words) |
| **CTA** | Optional (15-30 words) | 1 short line (10-20 chars) | 1 line (10-20 words) |
| **Sign-off** | 2 lines (name + company) | None | None |
| **Total Max** | 500 words | 300 characters | 200 words |

---

## Structure Templates

### Email Structure

```
{GREETING}

{BODY}

{CTA}

{SIGN_OFF}
```

**Greeting examples:**
- "Hi {customer_name},"
- "Hello {customer_name},"
- "Thanks for reaching out, {customer_name}!"

**Body format:**
- 3-5 complete sentences
- Use subheadings for complex issues (e.g., "Here's what I found:")
- Include specific links to docs/resources where applicable
- Address customer concern directly in first sentence

**CTA format (optional):**
- "Need more help? [Reply to this email / Chat with our team / Check our docs]"
- "Let me know if you have questions!"
- Only include if actionable next step exists

**Sign-off format:**
- Line 1: "Best regards," or "Thanks," or "Cheers,"
- Line 2: "Nova | NovaDeskAI Support"

---

### WhatsApp Structure

```
{BODY}
```

**Format rules:**
- NO greeting (too formal for WhatsApp)
- NO sign-off (not needed; conversation continuity visible)
- Conversational, like texting a friend
- Use emoji sparingly (max 1-2 per message) 😊
- Multiple short messages better than 1 long one
- Max 300 chars per message (WhatsApp best practice: 160 chars for readability)

---

### Web Chat Structure

```
{GREETING}

{BODY}

{CTA}
```

**Greeting format:**
- "Hi {customer_name}!" or "Hey there!" or "What can I help with?"
- Conversational but professional
- Single line only

**Body format:**
- 2-3 sentences (direct, semi-formal)
- Skip fluff; get to the point
- Use numbered steps for instructions

**CTA format (required):**
- Always include call-to-action
- "Click here to..." or "Reply below to..." or "Need more? Chat with our team →"

**Sign-off:**
- None needed (web chat is real-time)

---

## Issue-Type Templates

### 1. Password/Login Issues

#### Email Template

```
Hi {customer_name},

Thanks for letting me know about your login issue. I completely understand how frustrating that is when you just want to get started!

Here's what I'd recommend:
1. Try the password reset link on our login page (it sends a fresh reset email each time)
2. Check your spam folder for the reset email—it sometimes hides there
3. If the reset email doesn't arrive within 5 minutes, let me know and I can resend it

If you're still stuck after trying these steps, I'm here to help! You can also reply with your account email and I can check on our end.

Let me know how it goes!

Best regards,
Nova | NovaDeskAI Support
```

**Tone:** Empathetic, helpful, step-by-step  
**Length:** ~150 words ✅

#### WhatsApp Template

```
Got it! 🔐 Try the reset link on login page, check spam folder. Still stuck? Reply with your email and I'll help! 😊
```

**Tone:** Casual, concise  
**Length:** 98 chars ✅

#### Web Template

```
Hi there! 👋

I can definitely help you get back into your account. First, try the password reset link on our login page. If that doesn't work, check your spam folder—reset emails sometimes hide there. Let me know if you need anything else!

→ [Go to Password Reset](link)
```

**Tone:** Friendly, direct  
**Length:** ~75 words + CTA ✅

---

### 2. Billing Questions

#### Email Template

```
Hi {customer_name},

Thanks for your question about your invoice! I'm happy to help clarify.

Looking at your account, {SPECIFIC_BILLING_INFO}. Here's the breakdown:

- {LINE_ITEM_1}
- {LINE_ITEM_2}
- {LINE_ITEM_3}

{ADDITIONAL_CONTEXT}. If you believe this is an error, I can escalate this to our billing team for a full review.

Feel free to reply with any other questions!

Best regards,
Nova | NovaDeskAI Support
```

**Tone:** Professional, transparent, detailed  
**Length:** ~200 words ✅

#### WhatsApp Template

```
Got your billing question! 💰 Your invoice shows: {ITEMS}. Questions? Let me know! 📧
```

**Tone:** Direct, friendly  
**Length:** ~80 chars ✅

#### Web Template

```
Hi! 👋

I found your invoice. Here's what you're being charged for: {BREAKDOWN}. 

If you think there's an error, I can have our billing team look into it. Just let me know!

→ [View Your Invoice](link)
```

**Tone:** Professional, accessible  
**Length:** ~60 words ✅

---

### 3. Integration Problems

#### Email Template

```
Hi {customer_name},

Thanks for reaching out about the {INTEGRATION_NAME} integration. I can help!

I've checked our docs and here are the most common issues:

**Issue: {COMMON_ISSUE_1}**
Solution: {SOLUTION_1}

**Issue: {COMMON_ISSUE_2}**
Solution: {SOLUTION_2}

[If your issue doesn't match above:] I'd like to help further. Can you reply with:
1. The exact error message you're seeing (screenshot is helpful!)
2. When the integration last worked (if ever)
3. Any recent changes you made (settings, API keys, etc.)

Once I have those details, I can either solve it or escalate to our integration specialist.

Best regards,
Nova | NovaDeskAI Support
```

**Tone:** Technical but approachable, troubleshooting-focused  
**Length:** ~180 words ✅

#### WhatsApp Template

```
Ah, {INTEGRATION_NAME} issue! Common fix: {SOLUTION}. Still broken? Send me a screenshot 📸 of the error!
```

**Tone:** Problem-solving, casual  
**Length:** ~90 chars ✅

#### Web Template

```
I can help! The most common {INTEGRATION_NAME} issue is {ISSUE}. Try: {SOLUTION}.

If that doesn't work, send me a screenshot of the error and I'll dig deeper!

→ [View Integration Docs](link)
```

**Tone:** Action-oriented, supportive  
**Length:** ~60 words ✅

---

### 4. Bot Not Responding

#### Email Template

```
Hi {customer_name},

I'm sorry to hear the bot isn't responding—that's not the experience we want you to have!

Let me troubleshoot this with you:

**First, try these:**
1. Refresh the page (Ctrl+F5 for a hard refresh)
2. Clear browser cache and cookies
3. Try a different browser if you have one handy
4. Check your internet connection

**If it's still stuck:**
- Let me know what you see on screen (is there an error message?)
- What were you trying to do when it happened?
- What browser and device are you using?

In the meantime, I can help you directly via email. What's your question? I'd be happy to assist!

Best regards,
Nova | NovaDeskAI Support
```

**Tone:** Sympathetic, structured troubleshooting  
**Length:** ~150 words ✅

#### WhatsApp Template

```
Oh no! 😟 Try: refresh page, clear cache, different browser. Still stuck? Send screenshot & I'll help! 📱
```

**Tone:** Urgent, solutions-first  
**Length:** ~90 chars ✅

#### Web Template

```
That's frustrating! 😠 Try refreshing the page or clearing your browser cache. If that doesn't fix it, let me know what error you're seeing and I'll dig into it.

→ [Get Tech Support](link)
```

**Tone:** Empathetic, technical  
**Length:** ~50 words ✅

---

### 5. Onboarding Help

#### Email Template

```
Hi {customer_name},

Welcome to NovaDeskAI! 🎉 I'm excited to help you get set up.

Here's the quickest path to success:

**Step 1: [FIRST_TASK]** ({TIME})
> [Brief description + link to docs]

**Step 2: [SECOND_TASK]** ({TIME})
> [Brief description + link to docs]

**Step 3: [THIRD_TASK]** ({TIME})
> [Brief description + link to docs]

**Pro tip:** {USEFUL_FEATURE} can save you lots of time once you're set up.

I'm here if you get stuck on any step! Just reply, and I'll walk you through it.

Best regards,
Nova | NovaDeskAI Support
```

**Tone:** Enthusiastic, structured, encouraging  
**Length:** ~200 words ✅

#### WhatsApp Template

```
Welcome! 🎉 Get started in 3 steps: {STEP_1} → {STEP_2} → {STEP_3}. Questions? I'm here! 😊
```

**Tone:** Enthusiastic, concise  
**Length:** ~75 chars ✅

#### Web Template

```
Welcome! 🚀 Let's get you set up in 3 quick steps:

1. {STEP_1}
2. {STEP_2}
3. {STEP_3}

Once you're done, you'll be ready to roll! Need help with any step?

→ [Start Setup Guide](link)
```

**Tone:** Motivating, clear  
**Length:** ~70 words ✅

---

### 6. Escalation Handoff

#### Email Template

```
Hi {customer_name},

Thanks for your patience. I've reviewed your situation, and I think our {TEAM_NAME} specialist can give you the best solution.

Here's what I found and what I'm passing along:
- {CONTEXT_1}
- {CONTEXT_2}
- {CONTEXT_3}

{TEAM_NAME_PERSON} will be in touch within {TIME_SLA} with a full solution. They have all your details and context, so you won't need to repeat yourself.

In the meantime, if you have additional info, feel free to reply here and it'll reach the team.

Thanks for being a great customer!

Best regards,
Nova | NovaDeskAI Support
```

**Tone:** Reassuring, professional, transparent  
**Length:** ~150 words ✅

#### WhatsApp Template

```
Got it! 👍 Escalating to our specialists—they'll respond in {TIME}. You're in good hands! 😊
```

**Tone:** Confident, brief  
**Length:** ~70 chars ✅

#### Web Template

```
You got it! I'm escalating this to our {TEAM} team right now. Someone will respond within {TIME} with a solution.

Your info is all there, so no need to repeat yourself. We've got this! 💪

→ [Track Your Ticket](link)
```

**Tone:** Confident, supportive  
**Length:** ~65 words ✅

---

## Tone Guidelines by Channel

### Email Tone
- **Professional but warm:** balance business-like language with friendliness
- **Thorough:** provide context, examples, multiple options
- **Transparent:** explain why something happened or what you're doing
- **Formatted:** use structure (lists, bold headers) for scannability
- **Signature:** always include Nova's name + NovaDeskAI Support

**Avoid:**
- ❌ Overly casual ("hey yo")
- ❌ Too formal/robotic ("I acknowledge receipt of your inquiry")
- ❌ Walls of text (use bullet points, numbered lists)

---

### WhatsApp Tone
- **Conversational:** like texting a friend (but professional)
- **Concise:** one idea per message if possible
- **Emoji-friendly:** 1-2 relevant emoji per message max
- **Action-oriented:** lead with solution or next step
- **Fast:** short messages read faster

**Avoid:**
- ❌ Long paragraphs (break into separate messages)
- ❌ Complex formatting (bold/lists don't render well)
- ❌ Overly formal greetings ("Dear valued customer")
- ❌ Walls of emoji (looks spammy)

---

### Web Chat Tone
- **Semi-formal:** professional but approachable
- **Direct:** get to the point quickly
- **Interactive:** invite customer to click/reply
- **Helpful:** offer resources (docs, ticket tracking)
- **CTA-driven:** always have a clear next step

**Avoid:**
- ❌ Too casual (not email, but not a text)
- ❌ Too formal (feels distant on web chat)
- ❌ Vague next steps (always tell them what to do)

---

## Placeholder Variables (Available in All Channels)

| Placeholder | Description | Example |
|-------------|-------------|---------|
| `{customer_name}` | Customer's first name | "John" |
| `{company_name}` | Customer's company | "Acme Corp" |
| `{issue_type}` | Type of issue | "password reset" |
| `{INTEGRATION_NAME}` | Name of integration | "Slack", "Gmail" |
| `{TEAM_NAME}` | Team handling escalation | "Technical Support", "Billing" |
| `{TIME_SLA}` | Expected response time | "2 hours", "next business day" |
| `{TIME}` | Generic time reference | "30 minutes", "24 hours" |
| `{SPECIFIC_BILLING_INFO}` | Details from customer's account | "You're on Pro plan ($99/mo)" |
| `{SOLUTION}` | Specific solution based on issue | "Click 'Forgot Password'" |
| `{COMMON_ISSUE_1}` | First common variant | "API key not found" |
| `{SOLUTION_1}` | Solution to common issue 1 | "Generate new key in settings" |
| `{ERROR_MESSAGE}` | Exact error from system | "Connection timeout" |
| `{STEP_1}`, `{STEP_2}`, `{STEP_3}` | Onboarding steps | "Connect your email account" |
| `{ADDITIONAL_CONTEXT}` | Extra relevant info | "This includes your monthly subscription..." |

---

## Template Usage Guide

### When to Use Email Templates
- ✅ Formal escalations
- ✅ Detailed technical explanations needed
- ✅ Multiple steps/resources to share
- ✅ Customer initiated contact via email
- ❌ Urgent issues requiring <5 min response
- ❌ Simple yes/no questions

### When to Use WhatsApp Templates
- ✅ Quick, direct answers
- ✅ Urgent issues
- ✅ Casual, conversational tone
- ✅ Customer initiated contact via WhatsApp
- ❌ Complex integration setups
- ❌ Sensitive billing details (better in email)

### When to Use Web Chat Templates
- ✅ New customer interactions
- ✅ Mid-complexity issues
- ✅ Immediate support needed
- ✅ Customer using web form
- ❌ Long-term relationship building (email better)
- ❌ Sensitive personal info (WhatsApp or email better)

---

## Customization Rules

### Adding Customer Name
- **Email:** Always include in greeting ("Hi John,")
- **WhatsApp:** Optional, only if context appropriate ("Got it, John!")
- **Web:** Optional in greeting ("Hi John!" or generic "Hi there!")

### Adding Links/Resources
- **Email:** Full markdown links `[Link Text](URL)`
- **WhatsApp:** Just the URL (links auto-detect), or "Reply with YES for link"
- **Web:** Use arrow syntax `→ [Link Text](URL)` to denote CTAs

### Adapting for Issue Severity
- **Low severity (Password reset):** Keep tone light, 1-2 options
- **Medium severity (Integration issue):** More structured, troubleshooting steps
- **High severity (Data loss, security):** Escalate immediately, add empathy phrases

---

## Response Quality Checklist

Before sending any templated response, verify:

- [ ] **Grammar & Spelling:** No typos (critical for Email/Web, less so WhatsApp)
- [ ] **Placeholders filled:** All `{PLACEHOLDER}` values replaced with real data
- [ ] **Channel appropriate:** Tone, length, formatting match channel guidelines
- [ ] **Actionable:** Customer knows exactly what to do next
- [ ] **Empathetic:** Acknowledges customer pain point
- [ ] **Accurate:** Information matches current product state
- [ ] **No jargon:** Explain technical terms or avoid them
- [ ] **Branded:** Includes Nova + NovaDeskAI (Email/Web escalation only)

---

## Examples of Filled Templates

### Example 1: Email Password Reset (Low Severity)

```
Hi Sarah,

Thanks for letting me know about your login issue! I completely understand how frustrating that is when you just want to get started.

Here's what I'd recommend:
1. Try the password reset link on our login page (it sends a fresh reset email each time)
2. Check your spam folder for the reset email—it sometimes hides there
3. If the reset email doesn't arrive within 5 minutes, let me know and I can resend it

If you're still stuck after trying these steps, I'm here to help! You can also reply with your account email and I can check on our end.

Let me know how it goes!

Best regards,
Nova | NovaDeskAI Support
```

---

### Example 2: WhatsApp Integration Issue (Medium Severity)

```
Ah, Gmail integration issue! 🔧 Common fix: regenerate your Gmail API key in your account settings. If that doesn't work, send me a screenshot 📸 of the exact error!
```

---

### Example 3: Web Chat Escalation (High Severity)

```
I hear you, and I'm taking this seriously! 🎯 I'm escalating this to our senior technical team right now. They'll respond within 30 minutes with a solution.

Your full context is already with them, so you won't need to repeat anything.

→ [Track Your Ticket Here](link)
```

---

## Metrics to Track

Once deployed, measure template effectiveness by:

1. **First-Contact Resolution Rate:** % of issues resolved without escalation
2. **Customer Satisfaction (CSAT):** Post-chat survey after using template
3. **Response Time:** Avg time to deliver templated response (should be <5s)
4. **Escalation Rate:** % of conversations using each template that escalate anyway
5. **Sentiment Trend:** Does customer sentiment improve after templated response?

---

## Template Evolution

These templates should be refined based on real-world usage:

- **Weekly review:** Track which templates get highest CSAT
- **Monthly audit:** Identify commonly-asked questions not covered
- **Quarterly refresh:** Update links, product features, SLAs
- **Tag customer feedback:** "This template helped!" or "Needs improvement"

---

**Next Steps:**
- Test each template with 5+ real customer scenarios
- Gather feedback from support team on which templates feel most natural
- Refine language based on CSAT scores
- Create variations for different customer segments (enterprise vs. SMB)

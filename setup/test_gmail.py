"""
Gmail Webhook Test Script — NovaDeskAI
Simulates inbound Gmail Pub/Sub notifications without real Gmail.

Usage: python setup/test_gmail.py
"""
import os, sys, json, asyncio, base64
import httpx
from dotenv import load_dotenv
load_dotenv()

BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')

def make_pubsub_payload(email_data: dict) -> dict:
    """Encode a fake Gmail notification as a Pub/Sub push payload."""
    notification = json.dumps({"emailAddress": email_data["to"], "historyId": "12345"})
    encoded = base64.b64encode(notification.encode()).decode()
    return {
        "message": {
            "data": encoded,
            "messageId": f"msg-{email_data['id']}",
            "publishTime": "2026-02-27T10:00:00Z"
        },
        "subscription": "projects/novadesk/subscriptions/novadesk-gmail-sub"
    }

SAMPLE_EMAILS = [
    {
        "id": "001",
        "to": "support@novadesk.ai",
        "from_name": "Jane Smith",
        "from_email": "jane@example.com",
        "subject": "Cannot connect Gmail integration",
        "body": """Hi NovaDeskAI team,

I've been trying to connect my Gmail account to the NovaBot integration
for the past two days and it keeps failing with error code 403.

I've followed the documentation steps but the OAuth flow breaks at step 3.
My account is on the Growth plan.

Could you please help me resolve this?

Best regards,
Jane Smith"""
    },
    {
        "id": "002",
        "to": "support@novadesk.ai",
        "from_name": "Michael Torres",
        "from_email": "michael@startup.io",
        "subject": "Billing question — overcharged this month",
        "body": """Hello,

I noticed my invoice this month is $299 instead of the usual $149.
I'm on the Growth plan and haven't changed anything.

I believe this is an error. Can you please review my account and
issue a correction?

Invoice #INV-2026-0245

Thanks,
Michael Torres"""
    },
    {
        "id": "003",
        "to": "support@novadesk.ai",
        "from_name": "Sarah Chen",
        "from_email": "sarah@acme.com",
        "subject": "URGENT: Bot completely down - affecting customers",
        "body": """This is absolutely unacceptable!

Our NovaBot has been DOWN for 3 hours and we're losing customers.
We pay $499/month for the Scale plan and this is the THIRD outage
this month. I want to speak to a manager IMMEDIATELY.

If this isn't resolved in 1 hour, we're cancelling our subscription
and I will be contacting our legal team.

Sarah Chen
VP Operations, ACME Corp"""
    }
]

async def test_health():
    print("\n[TEST 0] API Health Check")
    print("-" * 40)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BASE_URL}/health")
            data = resp.json()
            print(f"  Status  : {data.get('status')}")
            print(f"  Version : {data.get('version')}")
            print(f"  ✅ API is running!")
            return True
        except Exception as e:
            print(f"  ❌ API not reachable at {BASE_URL}")
            print(f"     Run: python production/api/main.py")
            return False

async def test_gmail_webhook(email: dict):
    print(f"\n[TEST] Simulated Gmail Email")
    print(f"  From   : {email['from_name']} <{email['from_email']}>")
    print(f"  Subject: {email['subject']}")
    print(f"  Preview: {email['body'][:80].strip()}...")
    print("-" * 40)

    # Simulate what the agent would do with a direct process call
    url = f"{BASE_URL}/api/messages/process"
    payload = {
        "message": email["body"],
        "channel": "email",
        "customer_id": f"cust_{email['from_email'].split('@')[0]}",
        "conversation_id": None
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            resp = await client.post(url, json=payload)
            if resp.status_code == 200:
                data = resp.json()
                print(f"  Sentiment     : {data.get('sentiment', 'N/A')}")
                print(f"  Escalated     : {data.get('escalated', False)}")
                print(f"  Conversation  : {data.get('conversation_id', 'N/A')}")
                print(f"\n  Nova's Response (Email Format):")
                print(f"  {'─' * 44}")
                response_text = data.get('formatted_response') or data.get('response', '')
                for line in response_text[:500].split('\n'):
                    print(f"  {line}")
                print(f"  {'─' * 44}")
                print(f"  ✅ PASS")
            else:
                print(f"  ❌ FAIL — Status: {resp.status_code}")
                print(f"     {resp.text[:200]}")
        except Exception as e:
            print(f"  ❌ ERROR — {e}")

async def main():
    print("=" * 50)
    print("  NovaDeskAI — Gmail Integration Test Suite")
    print("=" * 50)
    print(f"  Target: {BASE_URL}")
    print(f"  Simulating {len(SAMPLE_EMAILS)} inbound emails\n")

    healthy = await test_health()
    if not healthy:
        sys.exit(1)

    for email in SAMPLE_EMAILS:
        await test_gmail_webhook(email)
        await asyncio.sleep(2)  # pause between emails

    print("\n" + "=" * 50)
    print("  Gmail simulation complete!")
    print()
    print("  For REAL Gmail integration:")
    print("  1. python setup/gmail_oauth.py      (authorize)")
    print("  2. python setup/gmail_watch.py       (set up Pub/Sub)")
    print("  3. ngrok http 8000                   (expose webhook)")
    print("  4. Configure Pub/Sub push URL in Google Console")
    print("  5. Send a real email to your Gmail address!")
    print("=" * 50)

if __name__ == '__main__':
    asyncio.run(main())

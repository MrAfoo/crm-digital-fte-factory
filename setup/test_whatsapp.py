"""
WhatsApp Webhook Test Script — NovaDeskAI
Tests your WhatsApp webhook without needing a real phone.

Usage: python setup/test_whatsapp.py
"""
import os, sys, json, asyncio
import httpx
from dotenv import load_dotenv
load_dotenv()

BASE_URL = os.getenv('API_BASE_URL', 'http://localhost:8000')
VERIFY_TOKEN = os.getenv('WHATSAPP_VERIFY_TOKEN', 'novadesk_verify')

# Simulated WhatsApp webhook payload
SAMPLE_MESSAGES = [
    {
        "description": "Billing question (neutral)",
        "payload": {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "field": "messages",
                    "value": {
                        "messages": [{
                            "id": "wamid.test001",
                            "from": "15551234567",
                            "timestamp": "1709000000",
                            "type": "text",
                            "text": {"body": "Hi, where can I find my invoice?"}
                        }],
                        "contacts": [{"profile": {"name": "Alice Johnson"}, "wa_id": "15551234567"}]
                    }
                }]
            }]
        }
    },
    {
        "description": "Angry customer (escalation trigger)",
        "payload": {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "field": "messages",
                    "value": {
                        "messages": [{
                            "id": "wamid.test002",
                            "from": "15559876543",
                            "timestamp": "1709000001",
                            "type": "text",
                            "text": {"body": "This is ridiculous! Your bot broke my integration and I want to talk to a human NOW!"}
                        }],
                        "contacts": [{"profile": {"name": "Bob Smith"}, "wa_id": "15559876543"}]
                    }
                }]
            }]
        }
    },
    {
        "description": "Human agent request",
        "payload": {
            "object": "whatsapp_business_account",
            "entry": [{
                "changes": [{
                    "field": "messages",
                    "value": {
                        "messages": [{
                            "id": "wamid.test003",
                            "from": "15557654321",
                            "timestamp": "1709000002",
                            "type": "text",
                            "text": {"body": "human"}
                        }],
                        "contacts": [{"profile": {"name": "Carol White"}, "wa_id": "15557654321"}]
                    }
                }]
            }]
        }
    }
]

async def test_webhook_verification():
    print("\n[TEST 1] Webhook Verification (GET)")
    print("-" * 40)
    url = f"{BASE_URL}/webhook/whatsapp"
    params = {
        "hub.mode": "subscribe",
        "hub.verify_token": VERIFY_TOKEN,
        "hub.challenge": "challenge_abc123"
    }
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params)
            challenge_ok = resp.status_code == 200 and "challenge_abc123" in resp.text
            if challenge_ok:
                print(f"  ✅ PASS — Webhook verified! Challenge returned: {resp.text}")
            else:
                print(f"  ❌ FAIL — Status: {resp.status_code}, Body: {resp.text}")
        except Exception as e:
            print(f"  ❌ ERROR — {e}")
            print(f"     Is the server running at {BASE_URL}?")

async def test_incoming_message(msg_data: dict):
    print(f"\n[TEST] Incoming Message: {msg_data['description']}")
    print("-" * 40)
    url = f"{BASE_URL}/webhook/whatsapp"
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            resp = await client.post(url, json=msg_data['payload'])
            print(f"  Status : {resp.status_code}")
            body = resp.json()
            print(f"  Response: {json.dumps(body, indent=2)}")
            if resp.status_code == 200:
                print(f"  ✅ PASS")
            else:
                print(f"  ❌ FAIL")
        except Exception as e:
            print(f"  ❌ ERROR — {e}")

async def test_health():
    print("\n[TEST 0] API Health Check")
    print("-" * 40)
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{BASE_URL}/health")
            data = resp.json()
            print(f"  Status  : {data.get('status')}")
            print(f"  Version : {data.get('version')}")
            print(f"  Services: {data.get('services')}")
            print(f"  ✅ API is running!")
        except Exception as e:
            print(f"  ❌ API not reachable at {BASE_URL}")
            print(f"     Run: python production/api/main.py")
            return False
    return True

async def main():
    print("=" * 50)
    print("  NovaDeskAI — WhatsApp Webhook Test Suite")
    print("=" * 50)
    print(f"  Target: {BASE_URL}")
    print(f"  Verify Token: {VERIFY_TOKEN}")

    healthy = await test_health()
    if not healthy:
        sys.exit(1)

    await test_webhook_verification()

    for msg in SAMPLE_MESSAGES:
        await test_incoming_message(msg)
        await asyncio.sleep(1)  # brief pause between messages

    print("\n" + "=" * 50)
    print("  Tests complete!")
    print("  Check production/api/main.py logs for Nova's responses.")
    print("=" * 50)

if __name__ == '__main__':
    asyncio.run(main())

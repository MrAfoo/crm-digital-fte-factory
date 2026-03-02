# Gmail API Setup — NovaDeskAI

## Quick Setup (5 steps)
1. Go to console.cloud.google.com → Enable Gmail API + Pub/Sub API
2. Create OAuth credentials (Desktop app) → Download as gmail_credentials.json → move to setup/
3. Run: python setup/gmail_oauth.py  (opens browser, saves gmail_token.json)
4. Create Pub/Sub topic: novadesk-gmail-notifications
5. Run: python setup/gmail_watch.py

## Pub/Sub Subscription
- Delivery type: Push
- Endpoint: https://YOUR-NGROK.ngrok-free.app/webhook/gmail
- Grant gmail-api-push@system.gserviceaccount.com → Pub/Sub Publisher role

## Test
python setup/test_gmail.py

## Your Setup (already done)
- Gmail: affanali.2006aa@gmail.com
- Pub/Sub Topic: projects/ai-employee-488306/topics/novadesk-gmail-notifications
- Token: setup/gmail_token.json (saved)
- Watch: Active (History ID: 749198, renew every 7 days)

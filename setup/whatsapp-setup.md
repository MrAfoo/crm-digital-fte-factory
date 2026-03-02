# WhatsApp Cloud API Setup — NovaDeskAI
See the full setup guide in DEMO.md and setup/whatsapp-setup.md.

## Quick Setup (5 steps)
1. Go to developers.facebook.com → Create App → Add WhatsApp
2. Copy Phone Number ID + Temporary Access Token from API Setup page
3. Add to .env: WHATSAPP_TOKEN=EAAxxxx, WHATSAPP_PHONE_NUMBER_ID=12345
4. Run: ngrok http 8000
5. In Meta Console → WhatsApp → Configuration → Webhook:
   - Callback URL: https://YOUR-NGROK.ngrok-free.app/webhook/whatsapp
   - Verify Token: novadesk_verify
   - Click Verify and Save → Enable 'messages' field

## Test
python setup/test_whatsapp.py

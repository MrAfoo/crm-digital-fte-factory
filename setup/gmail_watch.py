"""
Gmail Pub/Sub Watch Setup — NovaDeskAI
Sets up Gmail push notifications to your Pub/Sub topic.
Run AFTER gmail_oauth.py.

Usage: python setup/gmail_watch.py
"""
import os, sys, json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from dotenv import load_dotenv
load_dotenv()

CREDENTIALS_PATH = os.getenv('GMAIL_CREDENTIALS_PATH', 'setup/gmail_credentials.json')
TOKEN_PATH       = os.getenv('GMAIL_TOKEN_PATH', 'setup/gmail_token.json')
PUBSUB_TOPIC     = os.getenv('GMAIL_PUBSUB_TOPIC', '')
SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
]

def main():
    try:
        from googleapiclient.discovery import build
        from google.oauth2.credentials import Credentials
    except ImportError:
        print("[ERROR] Run: pip install google-auth google-auth-oauthlib google-api-python-client")
        sys.exit(1)

    if not os.path.exists(TOKEN_PATH):
        print(f"[ERROR] Token not found at {TOKEN_PATH}")
        print("Run python setup/gmail_oauth.py first.")
        sys.exit(1)

    if not PUBSUB_TOPIC:
        print("[ERROR] GMAIL_PUBSUB_TOPIC not set in .env")
        print("Format: projects/YOUR_PROJECT_ID/topics/novadesk-gmail-notifications")
        sys.exit(1)

    creds   = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    service = build('gmail', 'v1', credentials=creds)

    print(f"[INFO] Setting up Gmail watch...")
    print(f"       Topic: {PUBSUB_TOPIC}")

    request_body = {
        'labelIds': ['INBOX'],
        'topicName': PUBSUB_TOPIC,
    }

    try:
        response = service.users().watch(userId='me', body=request_body).execute()
        print(f"\n[SUCCESS] Gmail watch set up!")
        print(f"          History ID : {response.get('historyId')}")
        print(f"          Expiration : {response.get('expiration')} ms (renew every 7 days)")
        print(f"\n[INFO] New emails to your inbox will now trigger:")
        print(f"       Pub/Sub topic -> your /webhook/gmail endpoint -> Nova agent")
        print(f"\n[NEXT STEP] Make sure your server + ngrok are running, then send a test email!")
    except Exception as e:
        print(f"\n[ERROR] Failed to set up watch: {e}")
        print("Check that gmail-api-push@system.gserviceaccount.com has Pub/Sub Publisher role.")

if __name__ == '__main__':
    main()

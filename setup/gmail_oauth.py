"""
Gmail OAuth2 Authorization Script — NovaDeskAI
Run this ONCE to authorize Gmail access and save token.

Usage: python setup/gmail_oauth.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from dotenv import load_dotenv
load_dotenv()

CREDENTIALS_PATH = os.getenv('GMAIL_CREDENTIALS_PATH', 'setup/gmail_credentials.json')
TOKEN_PATH = os.getenv('GMAIL_TOKEN_PATH', 'setup/gmail_token.json')

SCOPES = [
    'https://www.googleapis.com/auth/gmail.readonly',
    'https://www.googleapis.com/auth/gmail.send',
    'https://www.googleapis.com/auth/gmail.modify',
]

def main():
    try:
        from google_auth_oauthlib.flow import InstalledAppFlow
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        import pickle
    except ImportError:
        print("[ERROR] Google libraries not installed.")
        print("Run: pip install google-auth google-auth-oauthlib google-api-python-client")
        sys.exit(1)

    if not os.path.exists(CREDENTIALS_PATH):
        print(f"[ERROR] credentials.json not found at: {CREDENTIALS_PATH}")
        print("Download it from Google Cloud Console -> APIs & Services -> Credentials")
        sys.exit(1)

    creds = None

    # Load existing token if available
    if os.path.exists(TOKEN_PATH):
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
        print(f"[INFO] Existing token found at {TOKEN_PATH}")

    # Refresh or get new token
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("[INFO] Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("[INFO] Opening browser for OAuth2 authorization...")
            print("       Please log in with your Gmail account and grant permissions.")
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_PATH, SCOPES)
            creds = flow.run_local_server(port=0)

        # Save token for future use
        with open(TOKEN_PATH, 'w') as f:
            f.write(creds.to_json())
        print(f"\n[SUCCESS] Token saved to: {TOKEN_PATH}")
    else:
        print("[INFO] Token is valid — no re-authorization needed.")

    # Test the connection
    try:
        from googleapiclient.discovery import build
        service = build('gmail', 'v1', credentials=creds)
        profile = service.users().getProfile(userId='me').execute()
        email = profile.get('emailAddress')
        print(f"\n[SUCCESS] Connected to Gmail: {email}")
        print(f"          Total messages: {profile.get('messagesTotal', 'N/A')}")
        print(f"\nNovaDeskAI will monitor this inbox for customer support emails.")
        print(f"Update your .env: GMAIL_USER_ID=me")
    except Exception as e:
        print(f"\n[WARN] Could not fetch profile: {e}")
        print("Token saved but Gmail connection test failed.")

    print("\n[NEXT STEP] Run: python setup/gmail_watch.py")
    print("            This sets up Pub/Sub push notifications for new emails.")


if __name__ == '__main__':
    main()

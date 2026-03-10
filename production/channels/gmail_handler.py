"""
Gmail Channel Handler for NovaDeskAI.
Handles inbound email via Gmail API + Pub/Sub push notifications.
Sends replies via Gmail API.
"""
import asyncio
import base64
import email as email_lib
import json
import logging
import os
import re
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Try to import Google libraries
try:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build
    from google.cloud import pubsub_v1
    GMAIL_AVAILABLE = True
except ImportError:
    logger.warning("Google API libraries not installed. Gmail handler will not be available.")
    GMAIL_AVAILABLE = False


_HISTORY_ID_FILE = os.path.join(os.path.dirname(__file__), ".gmail_last_history_id")

def _load_last_history_id() -> str:
    """Load persisted historyId from disk."""
    try:
        if os.path.exists(_HISTORY_ID_FILE):
            val = open(_HISTORY_ID_FILE).read().strip()
            if val.isdigit():
                return val
    except Exception:
        pass
    return None

def _save_last_history_id(history_id: str):
    """Persist historyId to disk so it survives API restarts."""
    try:
        with open(_HISTORY_ID_FILE, 'w') as f:
            f.write(str(history_id))
    except Exception as e:
        logger.warning(f"Could not save historyId to disk: {e}")


class GmailHandler:
    """Handler for Gmail channel integration."""

    # Class-level last known historyId — persisted to disk across restarts
    _last_history_id: str = _load_last_history_id()

    def __init__(self, token_path: str = None):
        """Initialize Gmail handler with user token (oauth token, not app credentials)."""
        self.available = False
        if not GMAIL_AVAILABLE:
            logger.warning("Gmail API libraries not available")
            return
        
        # Use GMAIL_TOKEN_PATH (the user oauth token), not GMAIL_CREDENTIALS_PATH (the app secret)
        credentials_path = token_path or os.getenv('GMAIL_TOKEN_PATH') or os.getenv('GMAIL_CREDENTIALS_PATH')
        if not credentials_path:
            logger.warning("GMAIL_TOKEN_PATH not set. Gmail handler disabled.")
            return
        
        try:
            if os.path.exists(credentials_path):
                # Ensure token file has required 'type' field
                self._ensure_token_type(credentials_path)
                self.credentials = Credentials.from_authorized_user_file(credentials_path)
                # Refresh if expired
                if not self.credentials.valid and self.credentials.refresh_token:
                    try:
                        from google.auth.transport.requests import Request
                        self.credentials.refresh(Request())
                        self._save_token(credentials_path, self.credentials)
                        logger.info("Gmail credentials refreshed successfully")
                    except Exception as refresh_err:
                        logger.warning(f"Could not refresh Gmail token: {refresh_err}")
                self.service = build('gmail', 'v1', credentials=self.credentials)
                self.available = True
                logger.info("Gmail handler initialized successfully")
            else:
                logger.warning(f"Credentials file not found: {credentials_path}")
        except Exception as e:
            logger.error(f"Failed to initialize Gmail handler: {e}")

    def _ensure_token_type(self, path: str):
        """Ensure token file has required 'type': 'authorized_user' field."""
        try:
            with open(path) as f:
                data = json.load(f)
            if data.get('type') != 'authorized_user':
                data['type'] = 'authorized_user'
                with open(path, 'w') as f:
                    json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not ensure token type: {e}")

    def _save_token(self, path: str, credentials):
        """Save credentials preserving the 'type' field."""
        try:
            import json as _json
            data = _json.loads(credentials.to_json())
            data['type'] = 'authorized_user'
            with open(path, 'w') as f:
                _json.dump(data, f, indent=2)
        except Exception as e:
            logger.warning(f"Could not save token: {e}")
    
    async def setup_push_notifications(self, topic_name: str) -> dict:
        """Set up Gmail push notifications via Pub/Sub."""
        if not self.available:
            return {'error': 'Gmail handler not available'}
        
        try:
            request = {
                'labelIds': ['INBOX'],
                'topicName': topic_name,
                'labelFilterAction': 'include'
            }
            result = self.service.users().watch(userId='me', body=request).execute()
            logger.info(f"Gmail watch set up with topic {topic_name}")
            return result
        except Exception as e:
            logger.error(f"Failed to set up Gmail push notifications: {e}")
            return {'error': str(e)}
    
    async def process_notification(self, pubsub_message: dict) -> list:
        """Process incoming Pub/Sub notification from Gmail.
        
        pubsub_message is the inner 'message' dict from the Pub/Sub envelope:
        {
            "data": "<base64 encoded JSON with emailAddress and historyId>",
            "messageId": "...",
            "publishTime": "..."
        }
        """
        if not self.available:
            return []
        
        try:
            # Decode base64 'data' field to get historyId
            history_id = None
            if 'data' in pubsub_message:
                try:
                    decoded = base64.b64decode(pubsub_message['data']).decode('utf-8')
                    notification = json.loads(decoded)
                    history_id = notification.get('historyId')
                    email_address = notification.get('emailAddress', '')
                    logger.info(f"Gmail Pub/Sub notification for {email_address}, historyId={history_id}")
                except Exception as e:
                    logger.error(f"Failed to decode Pub/Sub data: {e}")

            # Fallback: historyId directly in message (for testing)
            if not history_id:
                history_id = pubsub_message.get('historyId')

            if not history_id:
                logger.warning("No historyId in Pub/Sub message")
                return []

            # Determine startHistoryId:
            # - Use the last processed historyId if we have one AND it's <= notification id
            # - If persisted ID > notification ID (corrupted), reset and use notification id - 1
            # - Otherwise fall back to notification historyId - 1 as safe minimum
            try:
                notif_int = int(history_id)
                if GmailHandler._last_history_id:
                    persisted_int = int(GmailHandler._last_history_id)
                    if persisted_int <= notif_int:
                        start_id = GmailHandler._last_history_id
                        logger.info(f"Using persisted startHistoryId={start_id}")
                    else:
                        # Persisted ID is ahead of notification — corrupted, reset
                        logger.warning(f"Persisted historyId {persisted_int} > notification {notif_int} — resetting")
                        start_id = str(notif_int - 1)
                        GmailHandler._last_history_id = None
                        _save_last_history_id(start_id)
                else:
                    start_id = str(max(1, notif_int - 1))
                    logger.info(f"No persisted historyId, using startId={start_id}")
            except (ValueError, TypeError):
                start_id = history_id

            # Get new messages since last history ID (no type filter — get all,
            # then we filter for INBOX messagesAdded ourselves)
            history = await asyncio.to_thread(
                lambda: self.service.users().history().list(
                    userId='me',
                    startHistoryId=start_id,
                ).execute()
            )

            # Get our own email address to filter out self-sent messages
            our_email = os.getenv("GMAIL_USER_EMAIL", "")
            if not our_email:
                try:
                    profile = await asyncio.to_thread(
                        lambda: self.service.users().getProfile(userId='me').execute()
                    )
                    our_email = profile.get("emailAddress", "").lower()
                except Exception:
                    pass

            messages = []
            seen_ids = set()
            history_records = history.get('history', [])
            for record in history_records:
                for msg_added in record.get('messagesAdded', []):
                    msg_id = msg_added['message']['id']
                    labels = msg_added['message'].get('labelIds', [])
                    if msg_id in seen_ids:
                        continue
                    seen_ids.add(msg_id)
                    # Only process INBOX messages — skip SENT, DRAFT, SPAM, no-label
                    if 'INBOX' not in labels:
                        logger.debug(f"Skipping {msg_id} — not INBOX (labels={labels})")
                        continue
                    # Skip messages sent by ourselves (prevent infinite loop)
                    if 'SENT' in labels:
                        logger.debug(f"Skipping {msg_id} — SENT by us")
                        continue
                    message = await self.get_message(msg_id)
                    if not message:
                        continue
                    # Double-check: skip if from our own address
                    sender = message.get("customer_email", "").lower()
                    if our_email and sender == our_email:
                        logger.info(f"Skipping {msg_id} — from ourselves ({sender})")
                        continue
                    # Skip system/automated emails (bounce notifications, mailer daemons etc)
                    skip_senders = [
                        'mailer-daemon@', 'postmaster@', 'noreply@', 'no-reply@',
                        'notifications@', 'bounce@', 'auto-reply@', 'donotreply@',
                    ]
                    if any(s in sender for s in skip_senders):
                        logger.info(f"Skipping {msg_id} — system/automated sender ({sender})")
                        continue
                    messages.append(message)

            # Save current historyId as baseline for next notification (persisted to disk)
            GmailHandler._last_history_id = history_id
            _save_last_history_id(history_id)
            logger.info(f"Processed {len(messages)} new emails (historyId={history_id}, startId={start_id})")
            return messages
        except Exception as e:
            logger.error(f"Failed to process Gmail notification: {e}")
            return []
    
    async def get_message(self, message_id: str) -> dict:
        """Fetch and parse a Gmail message."""
        if not self.available:
            return {}
        
        try:
            msg = await asyncio.to_thread(
                lambda: self.service.users().messages().get(
                    userId='me',
                    id=message_id,
                    format='full'
                ).execute()
            )
            
            headers = {h['name']: h['value'] for h in msg['payload'].get('headers', [])}
            body = self._extract_body(msg['payload'])
            
            return {
                'channel': 'email',
                'channel_message_id': message_id,
                'customer_email': self._extract_email(headers.get('From', '')),
                'customer_name': headers.get('From', '').split('<')[0].strip(),
                'subject': headers.get('Subject', ''),
                'content': self._strip_quoted_text(body),
                'received_at': datetime.now(timezone.utc).isoformat(),
                'thread_id': msg.get('threadId'),
                'metadata': {
                    'headers': headers,
                    'labels': msg.get('labelIds', [])
                }
            }
        except Exception as e:
            # 404 means the message was deleted/moved before we could fetch it — not a real error
            if hasattr(e, 'resp') and getattr(e.resp, 'status', None) == 404:
                logger.warning(f"Gmail message {message_id} no longer exists (404) — skipping")
            else:
                logger.error(f"Failed to get Gmail message {message_id}: {e}")
            return {}
    
    def _extract_body(self, payload: dict) -> str:
        """Extract text body from email payload."""
        try:
            # Try direct body first
            if 'body' in payload and payload['body'].get('data'):
                return base64.urlsafe_b64decode(payload['body']['data']).decode('utf-8')
            
            # Try multipart
            if 'parts' in payload:
                for part in payload['parts']:
                    if part['mimeType'] == 'text/plain' and 'body' in part and part['body'].get('data'):
                        return base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
            
            return ''
        except Exception as e:
            logger.error(f"Failed to extract email body: {e}")
            return ''
    
    def _extract_email(self, from_header: str) -> str:
        """Extract email address from From header."""
        try:
            match = re.search(r'<(.+?)>', from_header)
            return match.group(1) if match else from_header
        except Exception as e:
            logger.error(f"Failed to extract email: {e}")
            return from_header
    
    def _strip_quoted_text(self, body: str) -> str:
        """Remove quoted text and signatures from email body."""
        try:
            # Remove "On ... wrote:" patterns
            lines = body.split('\n')
            result = []
            skip = False
            
            for line in lines:
                if re.match(r'^On .* wrote:', line):
                    skip = True
                elif skip and line.startswith('>'):
                    continue
                elif skip and line.strip() == '':
                    skip = False
                
                if not skip and not line.startswith('>'):
                    result.append(line)
            
            return '\n'.join(result).strip()
        except Exception as e:
            logger.error(f"Failed to strip quoted text: {e}")
            return body
    
    async def send_reply(self, to_email: str, subject: str, body: str, thread_id: str = None) -> dict:
        """Send email reply."""
        if not self.available:
            return {'error': 'Gmail handler not available'}
        
        try:
            message = MIMEText(body)
            message['to'] = to_email
            message['subject'] = f"Re: {subject}" if not subject.startswith('Re:') else subject
            
            raw = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
            
            send_request = {'raw': raw}
            if thread_id:
                send_request['threadId'] = thread_id
            
            result = await asyncio.to_thread(
                lambda: self.service.users().messages().send(
                    userId='me',
                    body=send_request
                ).execute()
            )
            
            logger.info(f"Sent reply to {to_email}")
            return {
                'channel_message_id': result['id'],
                'delivery_status': 'sent'
            }
        except Exception as e:
            logger.error(f"Failed to send email reply: {e}")
            return {'error': str(e)}
    
    async def send_new_email(self, to_email: str, subject: str, body: str, customer_name: str = "") -> dict:
        """Send new email (not a reply)."""
        if not self.available:
            logger.error("Gmail handler not available — cannot send email")
            raise RuntimeError("Gmail handler not available")

        try:
            msg = MIMEMultipart('alternative')
            msg['to'] = f"{customer_name} <{to_email}>" if customer_name else to_email
            msg['subject'] = subject

            # Plain text part
            msg.attach(MIMEText(body, 'plain'))

            raw = base64.urlsafe_b64encode(msg.as_bytes()).decode('utf-8')

            result = await asyncio.to_thread(
                lambda: self.service.users().messages().send(
                    userId='me',
                    body={'raw': raw}
                ).execute()
            )

            logger.info(f"✅ Sent new email to {to_email} (id={result.get('id')})")
            return {
                'channel_message_id': result['id'],
                'delivery_status': 'sent'
            }
        except Exception as e:
            logger.error(f"Failed to send new email to {to_email}: {e}")
            raise
    
    def normalize_to_standard(self, gmail_message: dict) -> dict:
        """Convert Gmail message to standard format."""
        return {
            'channel': gmail_message.get('channel', 'email'),
            'channel_message_id': gmail_message.get('channel_message_id'),
            'customer_email': gmail_message.get('customer_email'),
            'customer_name': gmail_message.get('customer_name'),
            'subject': gmail_message.get('subject'),
            'content': gmail_message.get('content'),
            'received_at': gmail_message.get('received_at'),
            'metadata': gmail_message.get('metadata', {})
        }


async def handle_gmail_webhook(request_body: dict) -> list:
    """Process Gmail Pub/Sub push notification from FastAPI endpoint."""
    try:
        handler = GmailHandler()
        if not handler.available:
            logger.warning("Gmail handler not available")
            return []
        
        messages = await handler.process_notification(request_body)
        return [handler.normalize_to_standard(msg) for msg in messages]
    except Exception as e:
        logger.error(f"Failed to handle Gmail webhook: {e}")
        return []

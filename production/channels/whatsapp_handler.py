"""
WhatsApp Cloud API Handler for NovaDeskAI.
Uses Meta WhatsApp Cloud API (free) instead of Twilio.
Webhook: POST /webhook/whatsapp
Verification: GET /webhook/whatsapp
"""
import hashlib
import hmac
import json
import logging
import os
import httpx
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

WHATSAPP_API_URL = 'https://graph.facebook.com/v18.0'


class WhatsAppHandler:
    """Handler for WhatsApp Cloud API channel integration."""

    # Class-level deduplication — track processed message IDs
    _processed_ids: set = set()

    def __init__(self):
        """Initialize WhatsApp handler with credentials from environment."""
        self.whatsapp_token = os.getenv('WHATSAPP_TOKEN', '')
        self.phone_number_id = os.getenv('WHATSAPP_PHONE_NUMBER_ID', '')
        self.verify_token = os.getenv('WHATSAPP_VERIFY_TOKEN', '')
        self.available = bool(self.whatsapp_token and self.phone_number_id)
        
        if self.available:
            logger.info("WhatsApp handler initialized successfully")
        else:
            logger.warning("WhatsApp credentials not fully configured. Handler disabled.")
    
    def verify_webhook(self, mode: str, token: str, challenge: str) -> Optional[str]:
        """Verify webhook subscription challenge from Meta."""
        if token != self.verify_token:
            logger.warning("Invalid verify token received")
            return None
        
        if mode == 'subscribe':
            logger.info("Webhook verified successfully")
            return challenge
        
        return None
    
    def validate_signature(self, payload_body: bytes, signature: str) -> bool:
        """Validate X-Hub-Signature-256 from Meta.
        
        Meta signs webhooks using the App Secret (not the access token).
        Set WHATSAPP_APP_SECRET in your .env from Meta App Dashboard:
        App Dashboard → Settings → Basic → App Secret
        """
        app_secret = os.getenv('WHATSAPP_APP_SECRET', '')
        if not app_secret:
            logger.warning("WHATSAPP_APP_SECRET not set — skipping signature validation (dev mode)")
            return True

        try:
            # Strip 'sha256=' prefix if present
            incoming = signature[7:] if signature.startswith('sha256=') else signature

            expected = hmac.new(
                app_secret.encode('utf-8'),
                payload_body,
                hashlib.sha256
            ).hexdigest()

            # Debug log to help diagnose mismatches
            if incoming != expected:
                logger.warning(
                    f"WhatsApp signature mismatch!\n"
                    f"  Incoming : {incoming[:20]}...\n"
                    f"  Expected : {expected[:20]}...\n"
                    f"  Secret   : {app_secret[:4]}****\n"
                    f"  Body len : {len(payload_body)} bytes\n"
                    f"  Tip: Verify WHATSAPP_APP_SECRET matches Meta App Dashboard → Settings → Basic → App Secret"
                )

            return hmac.compare_digest(incoming, expected)
        except Exception as e:
            logger.error(f"Failed to validate WhatsApp signature: {e}")
            return False
    
    async def process_webhook(self, webhook_data: dict) -> list:
        """Parse incoming WhatsApp webhook payload and extract messages."""
        try:
            messages = []
            
            # Parse webhook data structure
            if webhook_data.get('object') == 'whatsapp_business_account':
                for entry in webhook_data.get('entry', []):
                    for change in entry.get('changes', []):
                        if change['field'] == 'messages':
                            value = change.get('value', {})
                            
                            # Process incoming messages
                            for message in value.get('messages', []):
                                contact = value.get('contacts', [{}])[0]
                                parsed_msg = self._parse_message(message, contact)
                                if parsed_msg:
                                    messages.append(parsed_msg)
            
            logger.info(f"Processed {len(messages)} WhatsApp messages")
            return messages
        except Exception as e:
            logger.error(f"Failed to process WhatsApp webhook: {e}")
            return []
    
    def _parse_message(self, message: dict, contact: dict) -> Optional[dict]:
        """Parse single message object from WhatsApp."""
        try:
            message_type = message.get('type', 'text')
            message_id = message.get('id', '')
            from_phone = message.get('from', '')
            timestamp = message.get('timestamp', '')

            # Deduplication — skip already-processed messages
            if message_id and message_id in WhatsAppHandler._processed_ids:
                logger.info(f"Skipping duplicate WhatsApp message: {message_id}")
                return None
            if message_id:
                WhatsAppHandler._processed_ids.add(message_id)
                # Keep set from growing unbounded — trim to last 1000
                if len(WhatsAppHandler._processed_ids) > 1000:
                    WhatsAppHandler._processed_ids = set(
                        list(WhatsAppHandler._processed_ids)[-500:]
                    )
            
            content = ''
            if message_type == 'text':
                content = message.get('text', {}).get('body', '')
            elif message_type == 'image':
                content = f"[Image: {message.get('image', {}).get('caption', 'No caption')}]"
            elif message_type == 'document':
                doc = message.get('document', {})
                content = f"[Document: {doc.get('filename', 'Unknown')}]"
            elif message_type == 'audio':
                content = "[Audio message]"
            elif message_type == 'video':
                content = "[Video message]"
            elif message_type == 'location':
                loc = message.get('location', {})
                content = f"[Location: {loc.get('latitude')}, {loc.get('longitude')}]"
            
            return {
                'channel': 'whatsapp',
                'channel_message_id': message_id,
                'customer_phone': from_phone.replace('whatsapp:', ''),
                'customer_name': contact.get('profile', {}).get('name', 'Unknown'),
                'content': content,
                'received_at': datetime.fromtimestamp(int(timestamp), tz=timezone.utc).isoformat() if timestamp else datetime.now(timezone.utc).isoformat(),
                'metadata': {
                    'message_type': message_type,
                    'profile_name': contact.get('profile', {}).get('name'),
                    'wa_id': contact.get('wa_id')
                }
            }
        except Exception as e:
            logger.error(f"Failed to parse WhatsApp message: {e}")
            return None
    
    async def send_text_message(self, to_phone: str, body: str) -> dict:
        """Send text message via WhatsApp Cloud API."""
        if not self.available:
            return {'error': 'WhatsApp handler not available'}
        
        try:
            # Ensure phone number format
            if not to_phone.startswith('+'):
                to_phone = f'+{to_phone}'
            
            url = f"{WHATSAPP_API_URL}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.whatsapp_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messaging_product': 'whatsapp',
                'to': to_phone,
                'type': 'text',
                'text': {'body': body}
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Sent WhatsApp message to {to_phone}")
                    return {
                        'channel_message_id': result.get('messages', [{}])[0].get('id'),
                        'delivery_status': 'sent'
                    }
                else:
                    logger.error(f"Failed to send WhatsApp message: {response.text}")
                    return {'error': response.text}
        except Exception as e:
            logger.error(f"Failed to send WhatsApp message: {e}")
            return {'error': str(e)}
    
    async def send_template_message(self, to_phone: str, template_name: str, language: str = 'en_US') -> dict:
        """Send template message via WhatsApp Cloud API."""
        if not self.available:
            return {'error': 'WhatsApp handler not available'}
        
        try:
            if not to_phone.startswith('+'):
                to_phone = f'+{to_phone}'
            
            url = f"{WHATSAPP_API_URL}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.whatsapp_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messaging_product': 'whatsapp',
                'to': to_phone,
                'type': 'template',
                'template': {
                    'name': template_name,
                    'language': {'code': language}
                }
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"Sent WhatsApp template to {to_phone}")
                    return {
                        'channel_message_id': result.get('messages', [{}])[0].get('id'),
                        'delivery_status': 'sent'
                    }
                else:
                    logger.error(f"Failed to send WhatsApp template: {response.text}")
                    return {'error': response.text}
        except Exception as e:
            logger.error(f"Failed to send WhatsApp template: {e}")
            return {'error': str(e)}
    
    def format_response(self, response: str, max_length: int = 1600) -> list:
        """Format and split response for WhatsApp (max 1600 chars per message)."""
        if len(response) <= max_length:
            return [response]
        
        messages = []
        while response:
            if len(response) <= max_length:
                messages.append(response)
                break
            
            # Find a good break point
            break_point = response.rfind('. ', 0, max_length)
            if break_point == -1:
                break_point = response.rfind(' ', 0, max_length)
            if break_point == -1:
                break_point = max_length
            
            messages.append(response[:break_point + 1].strip())
            response = response[break_point + 1:].strip()
        
        return messages
    
    def normalize_to_standard(self, wa_message: dict) -> dict:
        """Convert WhatsApp message to standard format."""
        return {
            'channel': wa_message.get('channel', 'whatsapp'),
            'channel_message_id': wa_message.get('channel_message_id'),
            'customer_phone': wa_message.get('customer_phone'),
            'customer_name': wa_message.get('customer_name'),
            'content': wa_message.get('content'),
            'received_at': wa_message.get('received_at'),
            'metadata': wa_message.get('metadata', {})
        }
    
    async def mark_as_read(self, message_id: str) -> bool:
        """Mark message as read in WhatsApp."""
        if not self.available:
            return False
        
        try:
            url = f"{WHATSAPP_API_URL}/{self.phone_number_id}/messages"
            
            headers = {
                'Authorization': f'Bearer {self.whatsapp_token}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'messaging_product': 'whatsapp',
                'status': 'read',
                'message_id': message_id
            }
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, json=payload, headers=headers)
                
                if response.status_code == 200:
                    logger.info(f"Marked message {message_id} as read")
                    return True
                else:
                    logger.error(f"Failed to mark message as read: {response.text}")
                    return False
        except Exception as e:
            logger.error(f"Failed to mark message as read: {e}")
            return False


async def handle_whatsapp_webhook(webhook_data: dict) -> list:
    """Process WhatsApp webhook from FastAPI endpoint."""
    try:
        handler = WhatsAppHandler()
        if not handler.available:
            logger.warning("WhatsApp handler not available")
            return []
        
        messages = await handler.process_webhook(webhook_data)
        return [handler.normalize_to_standard(msg) for msg in messages]
    except Exception as e:
        logger.error(f"Failed to handle WhatsApp webhook: {e}")
        return []

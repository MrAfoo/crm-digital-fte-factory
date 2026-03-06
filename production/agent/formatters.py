"""
Channel-specific response formatters for NovaDeskAI Customer Success Agent.
Handles formatting, validation, and truncation per channel requirements.
"""

import re
from typing import Optional
from production.agent.prompts import CHANNEL_RESPONSE_LIMITS


class ChannelFormatter:
    """Format agent responses for different communication channels."""

    def format(self, response: str, channel: str, customer_name: str = 'there') -> str:
        """
        Format response for the specified channel.
        
        Args:
            response: Raw response text from agent
            channel: Channel identifier ('email', 'whatsapp', 'web', 'web_form')
            customer_name: Customer name for personalization
            
        Returns:
            Formatted response ready for channel delivery
        """
        if channel == 'email':
            return self._format_email(response, customer_name)
        elif channel == 'whatsapp':
            return self._format_whatsapp(response)
        elif channel in ('web', 'web_form'):
            return self._format_web(response)
        else:
            return response

    def _format_email(self, response: str, customer_name: str) -> str:
        """
        Format response for email channel.
        - Strips existing greetings
        - Adds formal greeting with customer name
        - Adds signature
        - Enforces character limit
        """
        # Strip existing greetings
        cleaned = self._strip_existing_greeting(response)
        
        # Build formatted email
        formatted = f"Hi {customer_name},\n\n{cleaned}\n\nBest regards,\nNova | NovaDeskAI Support"
        
        # Enforce length limit
        return self.truncate_to_limit(formatted, 'email')

    def _format_whatsapp(self, response: str) -> str:
        """
        Format response for WhatsApp channel.
        - Conversational tone
        - Concise (truncate to 297 chars + '...' if needed)
        - Emoji allowed sparingly
        """
        # Remove formal signatures and greetings
        cleaned = self._strip_existing_greeting(response)
        cleaned = re.sub(r'Best regards,?\s*.*$', '', cleaned, flags=re.DOTALL).strip()
        cleaned = re.sub(r'Nova \| NovaDeskAI Support', '', cleaned).strip()
        
        # Truncate to limit
        limit = CHANNEL_RESPONSE_LIMITS['whatsapp']
        if len(cleaned) > limit:
            return cleaned[:limit - 3] + '...'
        return cleaned

    def _format_web(self, response: str) -> str:
        """
        Format response for web form channel.
        - Semi-formal tone
        - Add helpful CTA footer
        - Balance detail with readability
        """
        # Strip existing signatures
        cleaned = self._strip_existing_greeting(response)
        cleaned = re.sub(r'Best regards,?\s*.*$', '', cleaned, flags=re.DOTALL).strip()
        
        # Enforce length limit
        return self.truncate_to_limit(cleaned, 'web_form')

    def _strip_existing_greeting(self, text: str) -> str:
        """
        Remove existing greetings from text using regex.
        Matches: Dear, Hi, Hello, Greetings at start of text.
        """
        pattern = r'^(Dear|Hi|Hello|Greetings)[^\n]*,?\s*\n?'
        return re.sub(pattern, '', text, flags=re.IGNORECASE).strip()

    def validate_length(self, response: str, channel: str) -> bool:
        """
        Check if response is within channel limit.
        
        Args:
            response: Response text to validate
            channel: Channel identifier
            
        Returns:
            True if within limit, False otherwise
        """
        limit = CHANNEL_RESPONSE_LIMITS.get(channel, float('inf'))
        return len(response) <= limit

    def truncate_to_limit(self, response: str, channel: str) -> str:
        """
        Truncate response to channel character limit.
        
        Args:
            response: Response text to truncate
            channel: Channel identifier
            
        Returns:
            Truncated response (with '...' if needed)
        """
        limit = CHANNEL_RESPONSE_LIMITS.get(channel, float('inf'))
        
        if len(response) <= limit:
            return response
        
        # Truncate at word boundary if possible
        truncated = response[:limit - 3].rsplit(' ', 1)[0]
        return truncated + '...'

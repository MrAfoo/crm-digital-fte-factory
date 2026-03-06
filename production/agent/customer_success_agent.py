"""
NovaDeskAI Production Customer Success Agent.
Uses Groq function calling. Model is configured via GROQ_MODEL env var
(default: llama-3.1-8b-instant for token efficiency; set to
llama-3.3-70b-versatile for maximum quality).
"""

import asyncio
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Optional

from groq import AsyncGroq
from dotenv import load_dotenv

from production.agent.prompts import CUSTOMER_SUCCESS_SYSTEM_PROMPT
from production.agent.formatters import ChannelFormatter
from production.agent.tools import (
    get_tools_for_groq,
    search_knowledge_base,
    create_ticket,
    get_customer_history,
    escalate_to_human,
    send_response,
    KnowledgeSearchInput,
    CreateTicketInput,
    CustomerHistoryInput,
    EscalateInput,
    SendResponseInput,
)

load_dotenv()
logger = logging.getLogger(__name__)


# ============================================================================
# ConversationContext
# ============================================================================

@dataclass
class ConversationContext:
    """Holds conversation state and history."""
    conversation_id: str
    customer_id: str
    channel: str
    messages: list = field(default_factory=list)
    sentiment: str = "neutral"
    topics: list = field(default_factory=list)
    resolution_status: str = "open"
    failed_attempts: int = 0
    created_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    escalated: bool = False
    metadata: dict = field(default_factory=dict)


# ============================================================================
# CustomerSuccessAgent
# ============================================================================

class CustomerSuccessAgent:
    """Production agent for handling customer success interactions."""

    def __init__(self):
        """Initialize agent with Groq client and tools."""
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY environment variable not set")
        
        self.client = AsyncGroq(api_key=api_key)
        self.model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")
        self.tools = get_tools_for_groq()
        self.formatter = ChannelFormatter()
        self._contexts: dict[str, ConversationContext] = {}
        
        logger.info("CustomerSuccessAgent initialized")

    def _get_or_create_context(
        self,
        conversation_id: Optional[str],
        customer_id: str,
        channel: str
    ) -> ConversationContext:
        """Get existing context or create new one."""
        if conversation_id and conversation_id in self._contexts:
            return self._contexts[conversation_id]
        
        # Create new context
        conv_id = conversation_id or f"CONV-{uuid.uuid4().hex[:8].upper()}"
        context = ConversationContext(
            conversation_id=conv_id,
            customer_id=customer_id,
            channel=channel,
        )
        self._contexts[conv_id] = context
        return context

    def _build_system_prompt(self, context: ConversationContext) -> str:
        """Build system prompt with context variables filled in."""
        prompt = CUSTOMER_SUCCESS_SYSTEM_PROMPT
        
        # Fill in template variables
        prompt = prompt.replace("{customer_id}", context.customer_id)
        prompt = prompt.replace("{conversation_id}", context.conversation_id)
        prompt = prompt.replace("{channel}", context.channel)
        prompt = prompt.replace("{customer_name}", context.metadata.get("customer_name", "Customer"))
        prompt = prompt.replace("{ticket_subject}", context.metadata.get("ticket_subject", ""))
        
        return prompt

    async def _call_groq_with_tools(
        self,
        messages: list,
        tools: list,
        max_retries: int = 3,
    ) -> dict:
        """
        Call Groq API with function calling.
        Automatically retries on 429 rate-limit errors with backoff.
        Returns response dict with choices[0].message
        """
        import re as _re
        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    tools=tools,
                    tool_choice="auto",
                    max_tokens=1024,
                )
                return response
            except Exception as e:
                err_str = str(e)
                if "429" in err_str and attempt < max_retries - 1:
                    # Parse retry-after from error message, default 60s
                    match = _re.search(r'try again in ([0-9.]+)s', err_str)
                    wait = float(match.group(1)) + 2.0 if match else 60.0
                    wait = min(wait, 120.0)  # cap at 2 min
                    logger.warning(f"Rate limited (429). Retrying in {wait:.1f}s (attempt {attempt+1}/{max_retries})")
                    await asyncio.sleep(wait)
                else:
                    raise

    async def _execute_tool(self, tool_name: str, tool_args: dict) -> str:
        """Dispatch to correct tool function based on name."""
        try:
            if tool_name == "search_knowledge_base":
                result = await search_knowledge_base(KnowledgeSearchInput(**tool_args))
            elif tool_name == "create_ticket":
                result = await create_ticket(CreateTicketInput(**tool_args))
            elif tool_name == "get_customer_history":
                result = await get_customer_history(CustomerHistoryInput(**tool_args))
            elif tool_name == "escalate_to_human":
                result = await escalate_to_human(EscalateInput(**tool_args))
            elif tool_name == "send_response":
                result = await send_response(SendResponseInput(**tool_args))
            else:
                return json.dumps({"error": f"Unknown tool: {tool_name}"})
            
            return result if isinstance(result, str) else json.dumps(result)
        
        except Exception as e:
            logger.error(f"Tool execution error ({tool_name}): {e}")
            return json.dumps({"error": str(e)})

    async def run(
        self,
        message: str,
        channel: str,
        customer_id: str,
        conversation_id: Optional[str] = None,
        customer_name: str = "Customer",
    ) -> dict:
        """
        Run agent on customer message.
        
        Implements Groq function-calling loop:
        1. Add user message
        2. Call Groq with tools
        3. Loop through tool calls until final response
        4. Format response for channel
        5. Return result
        """
        import time
        start_time = time.time()
        
        # Get or create context
        context = self._get_or_create_context(conversation_id, customer_id, channel)
        context.metadata["customer_name"] = customer_name
        
        # Add user message to context and messages list
        context.messages.append({"role": "user", "content": message})
        messages = [
            {"role": "system", "content": self._build_system_prompt(context)},
            *context.messages,
        ]
        
        tool_calls_made = []
        final_response = None
        response = None  # Initialize so tokens_used never throws UnboundLocalError
        
        try:
            # Function calling loop
            while True:
                response = await self._call_groq_with_tools(messages, self.tools)
                message_obj = response.choices[0].message
                
                # Check if there are tool calls
                if hasattr(message_obj, 'tool_calls') and message_obj.tool_calls:
                    # Add assistant message with tool calls
                    messages.append({
                        "role": "assistant",
                        "content": message_obj.content or "",
                        "tool_calls": [
                            {
                                "id": tc.id,
                                "type": "function",
                                "function": {
                                    "name": tc.function.name,
                                    "arguments": tc.function.arguments,
                                }
                            }
                            for tc in message_obj.tool_calls
                        ]
                    })
                    
                    # Execute each tool call
                    for tool_call in message_obj.tool_calls:
                        tool_name = tool_call.function.name
                        tool_args = json.loads(tool_call.function.arguments)
                        
                        logger.info(f"Executing tool: {tool_name}")
                        tool_calls_made.append(tool_name)
                        
                        result = await self._execute_tool(tool_name, tool_args)
                        
                        # Update context based on tool results
                        try:
                            result_data = json.loads(result)
                            if isinstance(result_data, dict):
                                if result_data.get("escalated") or tool_name == "escalate_to_human":
                                    context.escalated = True
                                if result_data.get("sentiment"):
                                    context.sentiment = result_data["sentiment"]
                        except Exception:
                            pass
                        
                        # Add tool result
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call.id,
                            "content": result,
                        })
                else:
                    # Final response (no tool calls)
                    final_response = message_obj.content
                    break
        
        except Exception as e:
            err_str = str(e)
            if "429" in err_str:
                logger.warning(f"Agent rate limited after all retries: {e}")
                # Don't send an error — use the friendly fallback below
                final_response = None
            else:
                logger.error(f"Agent run error: {e}")
                final_response = None
        
        # Strip any leaked raw function call text (llama-3.1 quirk)
        if final_response:
            import re as _re
            # Remove <function=...>...</function> blocks
            final_response = _re.sub(r'<function=[^>]+>.*?</function>', '', final_response, flags=_re.DOTALL)
            # Remove <function=...>{...} inline calls
            final_response = _re.sub(r'<function=\w+>\{.*?\}', '', final_response, flags=_re.DOTALL)
            # Remove leftover "Let's try a more general search." type artifacts before tool text
            final_response = _re.sub(r'\n{3,}', '\n\n', final_response)
            final_response = final_response.strip()

        # Format response for channel
        fallback = (
            "Thank you for reaching out to NovaDeskAI! We have received your message and "
            "a member of our support team will be in touch with you shortly. "
            "For urgent issues, please reply to this message with URGENT in the subject line."
        )
        formatted_response = self.formatter.format(
            final_response or fallback,
            channel,
            customer_name
        )
        
        # Update context
        context.messages.append({"role": "assistant", "content": final_response})
        context.updated_at = datetime.now(timezone.utc).isoformat()
        
        latency_ms = int((time.time() - start_time) * 1000)
        
        return {
            "response": final_response,
            "formatted_response": formatted_response,
            "conversation_id": context.conversation_id,
            "channel": channel,
            "sentiment": context.sentiment,
            "escalated": context.escalated,
            "tool_calls_made": tool_calls_made,
            "tokens_used": getattr(getattr(response, 'usage', None), 'total_tokens', 0) if 'response' in locals() else 0,
            "latency_ms": latency_ms,
        }

    def get_context(self, conversation_id: str) -> Optional[ConversationContext]:
        """Retrieve stored conversation context."""
        return self._contexts.get(conversation_id)

    def list_contexts(self) -> list:
        """List all active conversation contexts."""
        return list(self._contexts.values())


# ============================================================================
# Demo / Main
# ============================================================================

async def main():
    """Demo with 3 test messages across channels."""
    
    # Test message 1: Email
    print("\n" + "="*70)
    print("TEST 1: Email Channel")
    print("="*70)
    result1 = await agent.run(
        message="Hi, I'm having trouble integrating NovaDeskAI with our Slack workspace. Can you help?",
        channel="email",
        customer_id="CUST001",
        customer_name="Alice Johnson",
    )
    print(f"Conversation ID: {result1['conversation_id']}")
    print(f"Tools Used: {result1['tool_calls_made']}")
    print(f"Latency: {result1['latency_ms']}ms")
    print("\nFormatted Response:")
    print(result1['formatted_response'])
    
    # Test message 2: WhatsApp
    print("\n" + "="*70)
    print("TEST 2: WhatsApp Channel")
    print("="*70)
    result2 = await agent.run(
        message="How much does the Pro plan cost?",
        channel="whatsapp",
        customer_id="CUST002",
        customer_name="Bob Chen",
    )
    print(f"Conversation ID: {result2['conversation_id']}")
    print(f"Tools Used: {result2['tool_calls_made']}")
    print(f"Latency: {result2['latency_ms']}ms")
    print("\nFormatted Response:")
    print(result2['formatted_response'])
    
    # Test message 3: Web Form
    print("\n" + "="*70)
    print("TEST 3: Web Form Channel")
    print("="*70)
    result3 = await agent.run(
        message="I need help setting up two-factor authentication on my account.",
        channel="web_form",
        customer_id="CUST003",
        customer_name="Carol White",
    )
    print(f"Conversation ID: {result3['conversation_id']}")
    print(f"Tools Used: {result3['tool_calls_made']}")
    print(f"Latency: {result3['latency_ms']}ms")
    print("\nFormatted Response:")
    print(result3['formatted_response'])
    
    print("\n" + "="*70)
    print("Demo Complete")
    print("="*70)


if __name__ == "__main__":
    agent = CustomerSuccessAgent()
    asyncio.run(main())

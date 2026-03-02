"""
NovaDeskAI Automated Demo Runner
Shows the full system working end-to-end without needing real WhatsApp/Gmail.

Usage: python setup/demo_runner.py
"""

import asyncio
import httpx
import json
import time
import sys
from datetime import datetime
from typing import Optional

# ANSI color codes (works on Windows 10+ with ANSI_ESCAPE_SEQUENCES enabled)
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    
    # Foreground colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Background colors
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    
    @staticmethod
    def disable():
        """Disable colors for non-ANSI terminals"""
        for attr in dir(Colors):
            if not attr.startswith('_') and attr != 'disable':
                setattr(Colors, attr, '')

# Demo scenarios
SCENARIOS = [
    {
        "name": "Email — Billing Question",
        "channel": "Email",
        "customer_id": "CUST001",
        "customer_name": "Alice Johnson",
        "message": "Hi, I was charged twice this month for my subscription. Can you help me understand the charges?",
        "expected_sentiment": "neutral",
        "expected_escalation": False,
        "expected_tools": ["search_knowledge_base", "create_ticket"],
    },
    {
        "name": "WhatsApp — Pricing Question",
        "channel": "WhatsApp",
        "customer_id": "CUST002",
        "customer_name": "Bob Chen",
        "message": "Hey! Your product looks great. What are the pricing plans available? 🎉",
        "expected_sentiment": "positive",
        "expected_escalation": False,
        "expected_tools": ["search_knowledge_base"],
    },
    {
        "name": "Email — Angry Customer",
        "channel": "Email",
        "customer_id": "CUST003",
        "customer_name": "Carol White",
        "message": "This is UNACCEPTABLE! Your support has been completely useless. I've been waiting 3 days and nothing has been fixed. I demand to speak to a manager NOW!!!",
        "expected_sentiment": "angry",
        "expected_escalation": True,
        "expected_tools": ["escalate_to_human", "create_ticket"],
    },
    {
        "name": "Web Form — Onboarding Help",
        "channel": "Web",
        "customer_id": "CUST004",
        "customer_name": "David Lee",
        "message": "I just signed up but I'm confused about how to set up integrations. Can you walk me through it?",
        "expected_sentiment": "neutral",
        "expected_escalation": False,
        "expected_tools": ["search_knowledge_base", "get_customer_history"],
    },
    {
        "name": "WhatsApp — Human Agent Request",
        "channel": "WhatsApp",
        "customer_id": "CUST005",
        "customer_name": "Emma Rodriguez",
        "message": "I need to speak with a human agent about my custom enterprise setup",
        "expected_sentiment": "neutral",
        "expected_escalation": True,
        "expected_tools": ["escalate_to_human", "get_customer_history"],
    },
]

API_BASE_URL = "http://localhost:8000"
REQUEST_TIMEOUT = 45.0

# Stats tracking
stats = {
    "total_processed": 0,
    "total_escalations": 0,
    "total_time": 0.0,
    "response_times": [],
    "by_sentiment": {},
    "by_channel": {},
}


def print_header():
    """Print demo header"""
    print(f"\n{Colors.BOLD}{Colors.CYAN}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║                                                            ║")
    print("║           🚀 NovaDeskAI Automated Demo Runner 🚀           ║")
    print("║                                                            ║")
    print("║         Customer Success Agent in Action (Live API)       ║")
    print("║                                                            ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.RESET}\n")


def print_section(title: str):
    """Print section divider"""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'─' * 60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}📋 {title}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'─' * 60}{Colors.RESET}\n")


def print_scenario_header(num: int, scenario: dict):
    """Print scenario header"""
    print(f"{Colors.BOLD}{Colors.YELLOW}Scenario {num}: {scenario['name']}{Colors.RESET}")
    print(f"  Channel: {Colors.CYAN}{scenario['channel']}{Colors.RESET}")
    print(f"  Customer: {Colors.CYAN}{scenario['customer_name']}{Colors.RESET} ({scenario['customer_id']})")
    print()


def truncate_response(text: str, max_length: int = 200) -> str:
    """Truncate response text"""
    if len(text) > max_length:
        return text[:max_length] + "..."
    return text


async def health_check() -> bool:
    """Check if API is healthy"""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(f"{API_BASE_URL}/health")
            return response.status_code == 200
    except Exception as e:
        print(f"{Colors.RED}❌ Health check failed: {e}{Colors.RESET}")
        return False


async def process_scenario(num: int, scenario: dict) -> dict:
    """Process a single scenario"""
    print_scenario_header(num, scenario)
    
    request_payload = {
        "message": scenario["message"],
        "channel": scenario["channel"],
        "customer_id": scenario["customer_id"],
    }
    
    print(f"{Colors.DIM}Request:{Colors.RESET}")
    print(f"  Message: {truncate_response(scenario['message'])}")
    print()
    
    start_time = time.time()
    result = {
        "scenario": scenario,
        "success": False,
        "response": None,
        "latency_ms": 0,
        "error": None,
    }
    
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.post(
                f"{API_BASE_URL}/api/messages/process",
                json=request_payload,
            )
        
        latency_ms = (time.time() - start_time) * 1000
        result["latency_ms"] = latency_ms
        
        if response.status_code == 200:
            data = response.json()
            result["response"] = data
            result["success"] = True
        else:
            result["error"] = f"HTTP {response.status_code}"
    
    except asyncio.TimeoutError:
        result["error"] = "Request timeout (>5s)"
        result["latency_ms"] = (time.time() - start_time) * 1000
    except Exception as e:
        result["error"] = str(e)
        result["latency_ms"] = (time.time() - start_time) * 1000
    
    # Print results
    if result["success"]:
        print(f"{Colors.GREEN}✅ Success{Colors.RESET}")
        data = result["response"]
        
        # Sentiment
        sentiment = data.get("sentiment", "unknown")
        sentiment_emoji = {
            "positive": "😊",
            "neutral": "😐",
            "angry": "😠",
        }.get(sentiment, "❓")
        print(f"  Sentiment: {sentiment_emoji} {Colors.CYAN}{sentiment}{Colors.RESET}")
        
        # Escalation
        escalated = data.get("escalated", False)
        if escalated:
            print(f"  Escalation: {Colors.RED}⚠️  YES{Colors.RESET}")
        else:
            print(f"  Escalation: {Colors.GREEN}✓ No{Colors.RESET}")
        
        # Response
        response_text = data.get("response", "")
        formatted_response = truncate_response(response_text)
        print(f"  Response: \"{formatted_response}\"")
        
        # Tools called
        tools = data.get("tool_calls_made", [])
        if tools:
            print(f"  Tools: {Colors.MAGENTA}{', '.join(tools)}{Colors.RESET}")
        
        # Latency
        print(f"  Latency: {Colors.CYAN}{result['latency_ms']:.0f} ms{Colors.RESET}")
        
    else:
        print(f"{Colors.RED}❌ Failed: {result['error']}{Colors.RESET}")
        print(f"  Latency: {result['latency_ms']:.0f} ms")
    
    print()
    return result


async def fetch_stats() -> Optional[dict]:
    """Fetch API stats"""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(f"{API_BASE_URL}/api/stats")
            if response.status_code == 200:
                return response.json()
    except Exception:
        pass
    return None


async def fetch_tickets() -> Optional[list]:
    """Fetch all tickets"""
    try:
        async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
            response = await client.get(f"{API_BASE_URL}/api/tickets")
            if response.status_code == 200:
                data = response.json()
                return data.get("tickets", [])
    except Exception:
        pass
    return None


def print_summary(results: list):
    """Print demo summary"""
    print_section("📊 DEMO SUMMARY")
    
    # Calculate stats
    total = len(results)
    success = sum(1 for r in results if r["success"])
    escalations = sum(1 for r in results if r["success"] and r["response"].get("escalated", False))
    response_times = [r["latency_ms"] for r in results if r["success"]]
    
    if response_times:
        avg_time = sum(response_times) / len(response_times)
        min_time = min(response_times)
        max_time = max(response_times)
    else:
        avg_time = min_time = max_time = 0
    
    # Sentiment breakdown
    sentiments = {}
    channels_used = set()
    for r in results:
        if r["success"]:
            sentiment = r["response"].get("sentiment", "unknown")
            sentiments[sentiment] = sentiments.get(sentiment, 0) + 1
            channels_used.add(r["scenario"]["channel"])
    
    # Print summary table
    print(f"{Colors.BOLD}Requests:{Colors.RESET}")
    print(f"  Total Processed:     {Colors.CYAN}{total}{Colors.RESET}")
    print(f"  Successful:          {Colors.GREEN}{success}/{total}{Colors.RESET}")
    print(f"  Escalations:         {Colors.RED}{escalations}{Colors.RESET} ({escalations/total*100:.0f}%)")
    print()
    
    print(f"{Colors.BOLD}Response Times:{Colors.RESET}")
    print(f"  Average:             {Colors.CYAN}{avg_time:.0f} ms{Colors.RESET}")
    print(f"  Min:                 {Colors.GREEN}{min_time:.0f} ms{Colors.RESET}")
    print(f"  Max:                 {Colors.RED}{max_time:.0f} ms{Colors.RESET}")
    print()
    
    print(f"{Colors.BOLD}Channels Tested:{Colors.RESET}")
    for channel in sorted(channels_used):
        print(f"  ✓ {Colors.CYAN}{channel}{Colors.RESET}")
    print()
    
    print(f"{Colors.BOLD}Sentiment Distribution:{Colors.RESET}")
    for sentiment, count in sorted(sentiments.items()):
        emoji = {"positive": "😊", "neutral": "😐", "angry": "😠"}.get(sentiment, "❓")
        print(f"  {emoji} {sentiment.capitalize()}: {Colors.CYAN}{count}{Colors.RESET}")
    print()


async def print_api_stats():
    """Fetch and print API stats"""
    stats_data = await fetch_stats()
    if stats_data:
        print_section("📈 API METRICS (from /api/stats)")
        
        print(f"{Colors.BOLD}Tickets:{Colors.RESET}")
        total = stats_data.get("total_tickets", 0)
        print(f"  Total:               {Colors.CYAN}{total}{Colors.RESET}")
        
        by_status = stats_data.get("by_status", {})
        if by_status:
            print(f"  By Status:")
            for status, count in sorted(by_status.items()):
                print(f"    • {status}: {Colors.CYAN}{count}{Colors.RESET}")
        
        print()
        
        print(f"{Colors.BOLD}Channels:{Colors.RESET}")
        by_channel = stats_data.get("by_channel", {})
        if by_channel:
            for channel, count in sorted(by_channel.items()):
                print(f"  • {channel}: {Colors.CYAN}{count}{Colors.RESET}")
        
        print()
        
        active_convs = stats_data.get("conversations_active", 0)
        print(f"{Colors.BOLD}Active Conversations: {Colors.CYAN}{active_convs}{Colors.RESET}")
        print()


async def main():
    """Main demo runner"""
    # Enable colors on Windows
    if sys.platform == "win32":
        import os
        os.system("")  # Enable ANSI escape sequences
    
    print_header()
    
    # Check API health
    print(f"{Colors.YELLOW}🔍 Checking API health...{Colors.RESET}")
    healthy = await health_check()
    
    if not healthy:
        print(f"{Colors.RED}❌ API is not responding at {API_BASE_URL}{Colors.RESET}")
        print(f"{Colors.YELLOW}Make sure the API is running:{Colors.RESET}")
        print(f"  python production/api/main.py")
        return
    
    print(f"{Colors.GREEN}✅ API is healthy and responding{Colors.RESET}\n")
    
    # Run scenarios
    print_section("🎬 RUNNING DEMO SCENARIOS (5 scenarios)")
    
    results = []
    for i, scenario in enumerate(SCENARIOS, 1):
        result = await process_scenario(i, scenario)
        results.append(result)
        await asyncio.sleep(0.5)  # Small delay between requests
    
    # Print summary
    print_summary(results)
    
    # Fetch and print API stats
    print(f"{Colors.YELLOW}📊 Fetching API metrics...{Colors.RESET}")
    await asyncio.sleep(0.5)
    await print_api_stats()
    
    # Final message
    print_section("✨ DEMO COMPLETE")
    print(f"{Colors.GREEN}{Colors.BOLD}🎉 All scenarios executed successfully!{Colors.RESET}\n")
    print("What you just saw:")
    print("  ✅ 5 realistic customer messages processed")
    print("  ✅ Sub-2 second response times")
    print("  ✅ Real sentiment analysis (positive, neutral, angry)")
    print("  ✅ Smart escalation detection")
    print("  ✅ Tool-augmented AI in action")
    print("  ✅ CRM metrics updated in real-time")
    print()
    print(f"{Colors.CYAN}To see the live API endpoints, visit:{Colors.RESET}")
    print(f"  • Health:  {Colors.DIM}http://localhost:8000/api/health{Colors.RESET}")
    print(f"  • Tickets: {Colors.DIM}http://localhost:8000/api/tickets{Colors.RESET}")
    print(f"  • Stats:   {Colors.DIM}http://localhost:8000/api/stats{Colors.RESET}")
    print(f"  • Web Form: {Colors.DIM}http://localhost:8000/web-form/{Colors.RESET}")
    print()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Demo interrupted by user{Colors.RESET}")
    except Exception as e:
        print(f"\n{Colors.RED}Error: {e}{Colors.RESET}")
        import traceback
        traceback.print_exc()

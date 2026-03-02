"""
Database query functions for NovaDeskAI production system.
Uses asyncpg for async PostgreSQL access.
Falls back to in-memory store when DATABASE_URL not set.
"""
import asyncpg
import json
import uuid
import logging
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv
import os

load_dotenv()

logger = logging.getLogger(__name__)
DATABASE_URL = os.getenv('DATABASE_URL', '')

# In-memory fallback stores
_db_customers = {}
_db_conversations = {}
_db_messages = {}
_db_tickets = {}
_db_metrics = []

_pool: Optional[asyncpg.Pool] = None


async def get_pool() -> Optional[asyncpg.Pool]:
    """Create or return connection pool."""
    global _pool
    if not DATABASE_URL:
        logger.warning("DATABASE_URL not set. Using in-memory fallback.")
        return None
    
    if _pool is None:
        try:
            _pool = await asyncpg.create_pool(DATABASE_URL, min_size=5, max_size=20)
            logger.info("Database connection pool created successfully")
        except Exception as e:
            logger.error(f"Failed to create database pool: {e}")
            return None
    
    return _pool


async def create_customer(email: str, name: str, phone: str = None, metadata: dict = None) -> dict:
    """Create a new customer."""
    if metadata is None:
        metadata = {}
    
    customer_id = str(uuid.uuid4())
    
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO customers (id, email, phone, name, metadata)
                    VALUES ($1, $2, $3, $4, $5)
                    """,
                    customer_id, email, phone, name, json.dumps(metadata)
                )
                logger.info(f"Created customer {customer_id}")
        except Exception as e:
            logger.error(f"Failed to create customer: {e}")
    else:
        # In-memory fallback
        _db_customers[customer_id] = {
            'id': customer_id,
            'email': email,
            'phone': phone,
            'name': name,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'metadata': metadata
        }
    
    return {
        'id': customer_id,
        'email': email,
        'phone': phone,
        'name': name,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'metadata': metadata
    }


async def get_customer_by_email(email: str) -> Optional[dict]:
    """Get customer by email address."""
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT id, email, phone, name, created_at, metadata FROM customers WHERE email = $1",
                    email
                )
                if row:
                    return dict(row)
        except Exception as e:
            logger.error(f"Failed to get customer by email: {e}")
    else:
        # In-memory fallback
        for customer in _db_customers.values():
            if customer['email'] == email:
                return customer
    
    return None


async def get_customer_by_id(customer_id: str) -> Optional[dict]:
    """Get customer by ID."""
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                row = await conn.fetchrow(
                    "SELECT id, email, phone, name, created_at, metadata FROM customers WHERE id = $1",
                    customer_id
                )
                if row:
                    return dict(row)
        except Exception as e:
            logger.error(f"Failed to get customer by ID: {e}")
    else:
        # In-memory fallback
        return _db_customers.get(customer_id)
    
    return None


async def upsert_customer(email: str, name: str, phone: str = None) -> dict:
    """Insert or update a customer."""
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                # Try to get existing customer
                existing = await conn.fetchrow(
                    "SELECT id FROM customers WHERE email = $1",
                    email
                )
                
                if existing:
                    # Update existing
                    customer_id = existing['id']
                    await conn.execute(
                        "UPDATE customers SET name = $1, phone = $2 WHERE id = $3",
                        name, phone, customer_id
                    )
                else:
                    # Create new
                    customer_id = str(uuid.uuid4())
                    await conn.execute(
                        "INSERT INTO customers (id, email, phone, name) VALUES ($1, $2, $3, $4)",
                        customer_id, email, phone, name
                    )
                
                logger.info(f"Upserted customer {customer_id}")
                return await get_customer_by_id(customer_id) or {}
        except Exception as e:
            logger.error(f"Failed to upsert customer: {e}")
    else:
        # In-memory fallback
        for customer in _db_customers.values():
            if customer['email'] == email:
                customer['name'] = name
                customer['phone'] = phone
                return customer
        
        customer_id = str(uuid.uuid4())
        _db_customers[customer_id] = {
            'id': customer_id,
            'email': email,
            'phone': phone,
            'name': name,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'metadata': {}
        }
        return _db_customers[customer_id]
    
    return {}


async def create_conversation(customer_id: str, channel: str, metadata: dict = None) -> dict:
    """Create a new conversation."""
    if metadata is None:
        metadata = {}
    
    conversation_id = str(uuid.uuid4())
    
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO conversations (id, customer_id, initial_channel, metadata)
                    VALUES ($1, $2, $3, $4)
                    """,
                    conversation_id, customer_id, channel, json.dumps(metadata)
                )
                logger.info(f"Created conversation {conversation_id}")
        except Exception as e:
            logger.error(f"Failed to create conversation: {e}")
    else:
        # In-memory fallback
        _db_conversations[conversation_id] = {
            'id': conversation_id,
            'customer_id': customer_id,
            'initial_channel': channel,
            'started_at': datetime.now(timezone.utc).isoformat(),
            'status': 'active',
            'metadata': metadata
        }
    
    return {
        'id': conversation_id,
        'customer_id': customer_id,
        'initial_channel': channel,
        'started_at': datetime.now(timezone.utc).isoformat(),
        'status': 'active',
        'metadata': metadata
    }


async def update_conversation(conversation_id: str, status: str = None, sentiment_score: float = None,
                             resolution_type: str = None, escalated_to: str = None) -> bool:
    """Update conversation properties."""
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                updates = []
                params = []
                param_count = 1
                
                if status is not None:
                    updates.append(f"status = ${param_count}")
                    params.append(status)
                    param_count += 1
                if sentiment_score is not None:
                    updates.append(f"sentiment_score = ${param_count}")
                    params.append(sentiment_score)
                    param_count += 1
                if resolution_type is not None:
                    updates.append(f"resolution_type = ${param_count}")
                    params.append(resolution_type)
                    param_count += 1
                if escalated_to is not None:
                    updates.append(f"escalated_to = ${param_count}")
                    params.append(escalated_to)
                    param_count += 1
                
                if not updates:
                    return False
                
                params.append(conversation_id)
                query = f"UPDATE conversations SET {', '.join(updates)} WHERE id = ${param_count}"
                
                await conn.execute(query, *params)
                logger.info(f"Updated conversation {conversation_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update conversation: {e}")
            return False
    else:
        # In-memory fallback
        if conversation_id in _db_conversations:
            if status is not None:
                _db_conversations[conversation_id]['status'] = status
            if sentiment_score is not None:
                _db_conversations[conversation_id]['sentiment_score'] = sentiment_score
            if resolution_type is not None:
                _db_conversations[conversation_id]['resolution_type'] = resolution_type
            if escalated_to is not None:
                _db_conversations[conversation_id]['escalated_to'] = escalated_to
            return True
    
    return False


async def add_message(conversation_id: str, channel: str, direction: str, role: str, content: str,
                     tokens_used: int = None, latency_ms: int = None, tool_calls: list = None,
                     channel_message_id: str = None) -> dict:
    """Add a message to a conversation."""
    if tool_calls is None:
        tool_calls = []
    
    message_id = str(uuid.uuid4())
    
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO messages 
                    (id, conversation_id, channel, direction, role, content, tokens_used, latency_ms, tool_calls, channel_message_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
                    """,
                    message_id, conversation_id, channel, direction, role, content,
                    tokens_used, latency_ms, json.dumps(tool_calls), channel_message_id
                )
                logger.info(f"Added message {message_id}")
        except Exception as e:
            logger.error(f"Failed to add message: {e}")
    else:
        # In-memory fallback
        _db_messages[message_id] = {
            'id': message_id,
            'conversation_id': conversation_id,
            'channel': channel,
            'direction': direction,
            'role': role,
            'content': content,
            'created_at': datetime.now(timezone.utc).isoformat(),
            'tokens_used': tokens_used,
            'latency_ms': latency_ms,
            'tool_calls': tool_calls,
            'channel_message_id': channel_message_id,
            'delivery_status': 'pending'
        }
    
    return {
        'id': message_id,
        'conversation_id': conversation_id,
        'channel': channel,
        'direction': direction,
        'role': role,
        'content': content,
        'created_at': datetime.now(timezone.utc).isoformat(),
        'tokens_used': tokens_used,
        'latency_ms': latency_ms,
        'tool_calls': tool_calls,
        'channel_message_id': channel_message_id,
        'delivery_status': 'pending'
    }


async def get_conversation_messages(conversation_id: str) -> list:
    """Get all messages for a conversation."""
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, conversation_id, channel, direction, role, content, created_at,
                           tokens_used, latency_ms, tool_calls, channel_message_id, delivery_status
                    FROM messages WHERE conversation_id = $1 ORDER BY created_at
                    """,
                    conversation_id
                )
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get conversation messages: {e}")
    else:
        # In-memory fallback
        return [msg for msg in _db_messages.values() if msg['conversation_id'] == conversation_id]
    
    return []


async def create_ticket(conversation_id: str, customer_id: str, source_channel: str,
                       category: str = None, priority: str = 'medium') -> dict:
    """Create a support ticket."""
    ticket_id = str(uuid.uuid4())
    
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO tickets (id, conversation_id, customer_id, source_channel, category, priority)
                    VALUES ($1, $2, $3, $4, $5, $6)
                    """,
                    ticket_id, conversation_id, customer_id, source_channel, category, priority
                )
                logger.info(f"Created ticket {ticket_id}")
        except Exception as e:
            logger.error(f"Failed to create ticket: {e}")
    else:
        # In-memory fallback
        _db_tickets[ticket_id] = {
            'id': ticket_id,
            'conversation_id': conversation_id,
            'customer_id': customer_id,
            'source_channel': source_channel,
            'category': category,
            'priority': priority,
            'status': 'open',
            'created_at': datetime.now(timezone.utc).isoformat()
        }
    
    return {
        'id': ticket_id,
        'conversation_id': conversation_id,
        'customer_id': customer_id,
        'source_channel': source_channel,
        'category': category,
        'priority': priority,
        'status': 'open',
        'created_at': datetime.now(timezone.utc).isoformat()
    }


async def update_ticket(ticket_id: str, status: str = None, resolution_notes: str = None) -> bool:
    """Update a ticket."""
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                updates = []
                params = []
                param_count = 1
                
                if status is not None:
                    updates.append(f"status = ${param_count}")
                    params.append(status)
                    param_count += 1
                    if status == 'resolved':
                        updates.append(f"resolved_at = ${param_count}")
                        params.append(datetime.now(timezone.utc))
                        param_count += 1
                
                if resolution_notes is not None:
                    updates.append(f"resolution_notes = ${param_count}")
                    params.append(resolution_notes)
                    param_count += 1
                
                if not updates:
                    return False
                
                params.append(ticket_id)
                query = f"UPDATE tickets SET {', '.join(updates)} WHERE id = ${param_count}"
                
                await conn.execute(query, *params)
                logger.info(f"Updated ticket {ticket_id}")
                return True
        except Exception as e:
            logger.error(f"Failed to update ticket: {e}")
            return False
    else:
        # In-memory fallback
        if ticket_id in _db_tickets:
            if status is not None:
                _db_tickets[ticket_id]['status'] = status
                if status == 'resolved':
                    _db_tickets[ticket_id]['resolved_at'] = datetime.now(timezone.utc).isoformat()
            if resolution_notes is not None:
                _db_tickets[ticket_id]['resolution_notes'] = resolution_notes
            return True
    
    return False


async def get_customer_tickets(customer_id: str) -> list:
    """Get all tickets for a customer."""
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                rows = await conn.fetch(
                    """
                    SELECT id, conversation_id, customer_id, source_channel, category, priority,
                           status, created_at, resolved_at, resolution_notes
                    FROM tickets WHERE customer_id = $1 ORDER BY created_at DESC
                    """,
                    customer_id
                )
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to get customer tickets: {e}")
    else:
        # In-memory fallback
        return [ticket for ticket in _db_tickets.values() if ticket['customer_id'] == customer_id]
    
    return []


async def record_metric(metric_name: str, metric_value: float, channel: str = None, dimensions: dict = None) -> bool:
    """Record a performance metric."""
    if dimensions is None:
        dimensions = {}
    
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                await conn.execute(
                    """
                    INSERT INTO agent_metrics (metric_name, metric_value, channel, dimensions)
                    VALUES ($1, $2, $3, $4)
                    """,
                    metric_name, metric_value, channel, json.dumps(dimensions)
                )
                logger.debug(f"Recorded metric {metric_name}")
                return True
        except Exception as e:
            logger.error(f"Failed to record metric: {e}")
            return False
    else:
        # In-memory fallback
        _db_metrics.append({
            'metric_name': metric_name,
            'metric_value': metric_value,
            'channel': channel,
            'dimensions': dimensions,
            'recorded_at': datetime.now(timezone.utc).isoformat()
        })
        return True


async def get_metrics_summary() -> dict:
    """Get summary of collected metrics."""
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                # Get average response time
                avg_response = await conn.fetchval(
                    "SELECT AVG(metric_value) FROM agent_metrics WHERE metric_name = 'response_time_ms'"
                )
                
                # Get escalation count
                escalation_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM agent_metrics WHERE metric_name = 'escalation'"
                )
                
                # Get ticket count
                ticket_count = await conn.fetchval(
                    "SELECT COUNT(*) FROM tickets"
                )
                
                return {
                    'avg_response_time_ms': float(avg_response) if avg_response else 0,
                    'escalation_count': escalation_count or 0,
                    'ticket_count': ticket_count or 0
                }
        except Exception as e:
            logger.error(f"Failed to get metrics summary: {e}")
    else:
        # In-memory fallback
        response_times = [m['metric_value'] for m in _db_metrics if m['metric_name'] == 'response_time_ms']
        escalations = [m for m in _db_metrics if m['metric_name'] == 'escalation']
        
        avg_response = sum(response_times) / len(response_times) if response_times else 0
        
        return {
            'avg_response_time_ms': avg_response,
            'escalation_count': len(escalations),
            'ticket_count': len(_db_tickets)
        }
    
    return {}


async def search_knowledge_base(query_embedding: list, max_results: int = 5, category: str = None) -> list:
    """Search knowledge base using vector similarity."""
    pool = await get_pool()
    if pool:
        try:
            async with pool.acquire() as conn:
                # Vector similarity search using pgvector
                if category:
                    rows = await conn.fetch(
                        """
                        SELECT id, title, content, category, 1 - (embedding <=> $1::vector) as similarity
                        FROM knowledge_base
                        WHERE category = $2
                        ORDER BY embedding <=> $1::vector
                        LIMIT $3
                        """,
                        query_embedding, category, max_results
                    )
                else:
                    rows = await conn.fetch(
                        """
                        SELECT id, title, content, category, 1 - (embedding <=> $1::vector) as similarity
                        FROM knowledge_base
                        ORDER BY embedding <=> $1::vector
                        LIMIT $2
                        """,
                        query_embedding, max_results
                    )
                
                return [dict(row) for row in rows]
        except Exception as e:
            logger.error(f"Failed to search knowledge base: {e}")
    
    return []


async def close_pool():
    """Close database connection pool."""
    global _pool
    if _pool:
        try:
            await _pool.close()
            _pool = None
            logger.info("Database connection pool closed")
        except Exception as e:
            logger.error(f"Failed to close database pool: {e}")

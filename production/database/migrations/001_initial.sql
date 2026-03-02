BEGIN;

-- =============================================================================
-- CUSTOMER SUCCESS FTE - CRM/TICKET MANAGEMENT SYSTEM
-- NovaDeskAI Production Database Schema
-- =============================================================================
-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS vector; -- pgvector for semantic search

-- =============================================================================
-- CUSTOMERS TABLE (unified across channels) - YOUR CUSTOMER DATABASE
-- =============================================================================
CREATE TABLE customers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) UNIQUE,
    phone VARCHAR(50),
    name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    metadata JSONB DEFAULT '{}'
);

-- =============================================================================
-- CUSTOMER IDENTIFIERS TABLE (for cross-channel matching)
-- =============================================================================
CREATE TABLE customer_identifiers (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    identifier_type VARCHAR(50) NOT NULL, -- 'email', 'phone', 'whatsapp'
    identifier_value VARCHAR(255) NOT NULL,
    verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(identifier_type, identifier_value)
);

-- =============================================================================
-- CONVERSATIONS TABLE
-- =============================================================================
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    customer_id UUID REFERENCES customers(id),
    initial_channel VARCHAR(50) NOT NULL, -- 'email', 'whatsapp', 'web_form'
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    ended_at TIMESTAMP WITH TIME ZONE,
    status VARCHAR(50) DEFAULT 'active',
    sentiment_score DECIMAL(3,2),
    resolution_type VARCHAR(50),
    escalated_to VARCHAR(255),
    metadata JSONB DEFAULT '{}'
);

-- =============================================================================
-- MESSAGES TABLE (with channel tracking)
-- =============================================================================
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    channel VARCHAR(50) NOT NULL, -- 'email', 'whatsapp', 'web_form'
    direction VARCHAR(20) NOT NULL, -- 'inbound', 'outbound'
    role VARCHAR(20) NOT NULL, -- 'customer', 'agent', 'system'
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    tokens_used INTEGER,
    latency_ms INTEGER,
    tool_calls JSONB DEFAULT '[]',
    channel_message_id VARCHAR(255), -- External ID (Gmail message ID, Twilio SID)
    delivery_status VARCHAR(50) DEFAULT 'pending' -- 'pending', 'sent', 'delivered', 'failed'
);

-- =============================================================================
-- TICKETS TABLE
-- =============================================================================
CREATE TABLE tickets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id),
    customer_id UUID REFERENCES customers(id),
    source_channel VARCHAR(50) NOT NULL,
    category VARCHAR(100),
    priority VARCHAR(20) DEFAULT 'medium',
    status VARCHAR(50) DEFAULT 'open',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    resolved_at TIMESTAMP WITH TIME ZONE,
    resolution_notes TEXT
);

-- =============================================================================
-- KNOWLEDGE BASE TABLE
-- =============================================================================
CREATE TABLE knowledge_base (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(500) NOT NULL,
    content TEXT NOT NULL,
    category VARCHAR(100),
    embedding VECTOR(1536), -- For semantic search
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- CHANNEL CONFIGURATIONS TABLE
-- =============================================================================
CREATE TABLE channel_configs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    channel VARCHAR(50) UNIQUE NOT NULL,
    enabled BOOLEAN DEFAULT TRUE,
    config JSONB NOT NULL, -- API keys, webhook URLs, etc.
    response_template TEXT,
    max_response_length INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- AGENT PERFORMANCE METRICS TABLE
-- =============================================================================
CREATE TABLE agent_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(10,4) NOT NULL,
    channel VARCHAR(50), -- Optional: channel-specific metrics
    dimensions JSONB DEFAULT '{}',
    recorded_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =============================================================================
-- INDEXES FOR PERFORMANCE
-- =============================================================================
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customer_identifiers_value ON customer_identifiers(identifier_value);
CREATE INDEX idx_conversations_customer ON conversations(customer_id);
CREATE INDEX idx_conversations_status ON conversations(status);
CREATE INDEX idx_conversations_channel ON conversations(initial_channel);
CREATE INDEX idx_messages_conversation ON messages(conversation_id);
CREATE INDEX idx_messages_channel ON messages(channel);
CREATE INDEX idx_tickets_status ON tickets(status);
CREATE INDEX idx_tickets_channel ON tickets(source_channel);
CREATE INDEX idx_knowledge_embedding ON knowledge_base USING ivfflat (embedding vector_cosine_ops);

-- =============================================================================
-- SEED DATA - CHANNEL CONFIGURATIONS
-- =============================================================================
INSERT INTO channel_configs (channel, enabled, config, response_template, max_response_length)
VALUES
    (
        'email',
        true,
        '{"api": "gmail", "webhook_enabled": true}'::jsonb,
        'Dear {{customer_name}},\n\n{{message}}\n\nBest regards,\nNovaDeskAI Support Team',
        500
    ),
    (
        'whatsapp',
        true,
        '{"api": "meta", "webhook_enabled": true}'::jsonb,
        '{{message}}',
        300
    ),
    (
        'web_form',
        true,
        '{"api": "internal", "webhook_enabled": true}'::jsonb,
        'Thank you for your submission, {{customer_name}}. We will respond shortly.',
        300
    );

-- =============================================================================
-- SEED DATA - SAMPLE CUSTOMERS
-- =============================================================================
INSERT INTO customers (email, phone, name, metadata)
VALUES
    ('alice@example.com', '+1-555-0101', 'Alice Johnson', '{"account_type": "premium", "signup_date": "2024-01-15"}'::jsonb),
    ('bob@example.com', '+1-555-0102', 'Bob Smith', '{"account_type": "standard", "signup_date": "2024-02-20"}'::jsonb),
    ('charlie@example.com', '+1-555-0103', 'Charlie Brown', '{"account_type": "starter", "signup_date": "2024-03-10"}'::jsonb);

-- =============================================================================
-- SEED DATA - SAMPLE CUSTOMER IDENTIFIERS
-- =============================================================================
INSERT INTO customer_identifiers (customer_id, identifier_type, identifier_value, verified)
SELECT id, 'email', email, true FROM customers WHERE email = 'alice@example.com'
UNION ALL
SELECT id, 'phone', phone, true FROM customers WHERE email = 'alice@example.com'
UNION ALL
SELECT id, 'email', email, true FROM customers WHERE email = 'bob@example.com'
UNION ALL
SELECT id, 'phone', phone, true FROM customers WHERE email = 'bob@example.com'
UNION ALL
SELECT id, 'email', email, true FROM customers WHERE email = 'charlie@example.com'
UNION ALL
SELECT id, 'phone', phone, true FROM customers WHERE email = 'charlie@example.com';

COMMIT;

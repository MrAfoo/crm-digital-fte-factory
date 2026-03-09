# Kafka configuration for NovaDeskAI
from dataclasses import dataclass
import os

@dataclass
class KafkaConfig:
    bootstrap_servers: str = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    consumer_group_id: str = os.getenv('KAFKA_CONSUMER_GROUP', 'nova-agent-group')
    auto_offset_reset: str = 'earliest'
    max_poll_interval_ms: int = 300000
    session_timeout_ms: int = 10000
    enable_auto_commit: bool = True
    auto_commit_interval_ms: int = 1000

# Topic names — matches hackathon spec (fte.*)
TOPIC_TICKETS_INCOMING    = 'fte.tickets.incoming'
TOPIC_EMAIL_INBOUND       = 'fte.channels.email.inbound'
TOPIC_WHATSAPP_INBOUND    = 'fte.channels.whatsapp.inbound'
TOPIC_WEBFORM_INBOUND     = 'fte.channels.webform.inbound'
TOPIC_EMAIL_OUTBOUND      = 'fte.channels.email.outbound'
TOPIC_WHATSAPP_OUTBOUND   = 'fte.channels.whatsapp.outbound'
TOPIC_ESCALATIONS         = 'fte.escalations'
TOPIC_METRICS             = 'fte.metrics'
TOPIC_DLQ                 = 'fte.dlq'

# Legacy aliases (backward compat)
TOPIC_INBOUND   = TOPIC_TICKETS_INCOMING
TOPIC_PROCESSED = TOPIC_TICKETS_INCOMING
TOPIC_TICKETS   = TOPIC_TICKETS_INCOMING

TOPICS = {
    'tickets_incoming':  TOPIC_TICKETS_INCOMING,
    'email_inbound':     TOPIC_EMAIL_INBOUND,
    'whatsapp_inbound':  TOPIC_WHATSAPP_INBOUND,
    'webform_inbound':   TOPIC_WEBFORM_INBOUND,
    'email_outbound':    TOPIC_EMAIL_OUTBOUND,
    'whatsapp_outbound': TOPIC_WHATSAPP_OUTBOUND,
    'escalations':       TOPIC_ESCALATIONS,
    'metrics':           TOPIC_METRICS,
    'dlq':               TOPIC_DLQ,
}

# Default config instance
default_config = KafkaConfig()

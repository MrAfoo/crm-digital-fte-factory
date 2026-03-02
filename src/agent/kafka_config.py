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

# Topic names
TOPIC_INBOUND = 'nova.messages.inbound'
TOPIC_PROCESSED = 'nova.messages.processed'
TOPIC_ESCALATIONS = 'nova.escalations'
TOPIC_TICKETS = 'nova.tickets'
TOPIC_DLQ = 'nova.dlq'

# Default config instance
default_config = KafkaConfig()

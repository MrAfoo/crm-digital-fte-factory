"""
Kafka async message streaming layer for NovaDeskAI Customer Success Agent.
Uses confluent-kafka with graceful fallback to mock mode if not installed.
"""

import json
import logging
import threading
import time
import uuid
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import Callable, Optional, Dict, Any, List, Tuple
from enum import Enum

from kafka_config import (
    KafkaConfig, TOPIC_INBOUND, TOPIC_PROCESSED, TOPIC_ESCALATIONS, 
    TOPIC_TICKETS, TOPIC_DLQ, default_config
)

# Try to import confluent-kafka, fall back to mock if not available
try:
    from confluent_kafka import Producer, Consumer, KafkaError, admin
    from confluent_kafka.admin import AdminClient, NewTopic
    KAFKA_AVAILABLE = True
except ImportError:
    KAFKA_AVAILABLE = False
    logging.warning("confluent-kafka not installed. Running in MOCK mode.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ============================================================================
# MESSAGE SCHEMA
# ============================================================================

@dataclass
class KafkaMessage:
    """Kafka message schema for NovaDeskAI"""
    message_id: str          # UUID
    customer_id: str
    conversation_id: str
    channel: str             # email | whatsapp | web
    message_type: str        # inbound | processed | escalation | ticket
    payload: dict            # actual message content
    timestamp: str           # ISO format
    metadata: dict           # channel-specific metadata
    retry_count: int = 0
    max_retries: int = 3

    def to_json(self) -> str:
        """Serialize to JSON"""
        return json.dumps(asdict(self), default=str)

    @staticmethod
    def from_json(json_str: str) -> 'KafkaMessage':
        """Deserialize from JSON"""
        data = json.loads(json_str)
        return KafkaMessage(**data)

    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return asdict(self)


# ============================================================================
# MOCK PRODUCER/CONSUMER (for when confluent-kafka is not available)
# ============================================================================

class MockProducer:
    """Mock Kafka producer for development/testing"""
    
    def __init__(self, bootstrap_servers: str = 'localhost:9092'):
        self.bootstrap_servers = bootstrap_servers
        self.messages: List[Dict[str, Any]] = []
        logger.warning(f"MockProducer initialized (not connected to real Kafka)")
    
    def produce(self, topic: str, key: Optional[str], value: str, 
                callback: Optional[Callable] = None):
        """Mock produce - just logs and stores"""
        self.messages.append({
            'topic': topic,
            'key': key,
            'value': value,
            'timestamp': datetime.utcnow().isoformat()
        })
        logger.info(f"[MOCK] Produced to {topic}: {key}")
        if callback:
            callback(None, None)
    
    def poll(self, timeout_ms: int = 0):
        """Mock poll"""
        return None
    
    def flush(self, timeout: int = 10):
        """Mock flush"""
        logger.info(f"[MOCK] Flushed {len(self.messages)} messages")


class MockConsumer:
    """Mock Kafka consumer for development/testing"""
    
    def __init__(self, topics: List[str], group_id: str, 
                 bootstrap_servers: str = 'localhost:9092', 
                 auto_offset_reset: str = 'earliest'):
        self.topics = topics
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers
        self.running = False
        logger.warning(f"MockConsumer initialized for topics {topics}")
    
    def subscribe(self, topics: List[str]):
        """Mock subscribe"""
        logger.info(f"[MOCK] Subscribed to {topics}")
    
    def poll(self, timeout_ms: int = 1000):
        """Mock poll - returns None"""
        return None
    
    def close(self):
        """Mock close"""
        logger.info("[MOCK] Consumer closed")


# ============================================================================
# NOVA KAFKA PRODUCER
# ============================================================================

class NovaDeskProducer:
    """Kafka producer for NovaDeskAI with delivery guarantees"""
    
    def __init__(self, bootstrap_servers: str = 'localhost:9092'):
        """
        Initialize Kafka producer
        
        Args:
            bootstrap_servers: Kafka broker addresses
        """
        self.bootstrap_servers = bootstrap_servers
        self.kafka_available = KAFKA_AVAILABLE
        
        if self.kafka_available:
            try:
                config = {
                    'bootstrap.servers': bootstrap_servers,
                    'client.id': f'nova-producer-{uuid.uuid4().hex[:8]}',
                    'acks': 'all',  # Wait for all replicas
                    'retries': 3,
                    'retry.backoff.ms': 100,
                    'linger.ms': 10,  # Batch messages
                    'batch.size': 16384,
                }
                self.producer = Producer(config)
                logger.info(f"NovaDeskProducer initialized - {bootstrap_servers}")
            except Exception as e:
                logger.warning(f"Failed to initialize real Kafka producer: {e}. Using mock.")
                self.producer = MockProducer(bootstrap_servers)
                self.kafka_available = False
        else:
            self.producer = MockProducer(bootstrap_servers)
    
    def delivery_report(self, err, msg):
        """Delivery report callback"""
        if err is not None:
            logger.error(f"Message delivery failed: {err}")
        else:
            logger.debug(f"Message delivered to {msg.topic()} [{msg.partition()}]")
    
    def produce_message(self, topic: str, message: KafkaMessage) -> bool:
        """
        Produce a message to Kafka topic
        
        Args:
            topic: Target topic
            message: KafkaMessage instance
            
        Returns:
            True if produced successfully
        """
        try:
            json_payload = message.to_json()
            
            if self.kafka_available:
                self.producer.produce(
                    topic=topic,
                    key=message.message_id,
                    value=json_payload,
                    callback=self.delivery_report
                )
                self.producer.poll(0)  # Trigger callbacks
            else:
                self.producer.produce(
                    topic=topic,
                    key=message.message_id,
                    value=json_payload,
                    callback=self.delivery_report
                )
            
            logger.debug(f"Produced {message.message_type} to {topic}")
            return True
        except Exception as e:
            logger.error(f"Error producing message to {topic}: {e}")
            return False
    
    def produce_inbound(self, customer_id: str, conversation_id: str, 
                       channel: str, raw_message: str, 
                       metadata: Dict[str, Any] = None) -> bool:
        """
        Convenience method to produce inbound message
        
        Args:
            customer_id: Customer ID
            conversation_id: Conversation ID
            channel: Message channel (email, whatsapp, web)
            raw_message: Raw message content
            metadata: Channel-specific metadata
            
        Returns:
            True if produced successfully
        """
        message = KafkaMessage(
            message_id=str(uuid.uuid4()),
            customer_id=customer_id,
            conversation_id=conversation_id,
            channel=channel,
            message_type='inbound',
            payload={'raw_message': raw_message},
            timestamp=datetime.utcnow().isoformat(),
            metadata=metadata or {}
        )
        return self.produce_message(TOPIC_INBOUND, message)
    
    def produce_processed(self, original_message: KafkaMessage, 
                         agent_result: Dict[str, Any]) -> bool:
        """
        Produce processed agent result
        
        Args:
            original_message: Original inbound message
            agent_result: Result from agent_loop.process_message()
            
        Returns:
            True if produced successfully
        """
        message = KafkaMessage(
            message_id=str(uuid.uuid4()),
            customer_id=original_message.customer_id,
            conversation_id=agent_result.get('conversation_id', original_message.conversation_id),
            channel=original_message.channel,
            message_type='processed',
            payload=agent_result,
            timestamp=datetime.utcnow().isoformat(),
            metadata={
                'original_message_id': original_message.message_id,
                'escalated': agent_result.get('escalated', False),
                'sentiment': agent_result.get('sentiment', 'neutral'),
            }
        )
        return self.produce_message(TOPIC_PROCESSED, message)
    
    def produce_escalation(self, customer_id: str, conversation_id: str, 
                          channel: str, reason: str, tier: int, 
                          sentiment: str) -> bool:
        """
        Produce escalation event
        
        Args:
            customer_id: Customer ID
            conversation_id: Conversation ID
            channel: Message channel
            reason: Escalation reason
            tier: Escalation tier (1, 2, 3)
            sentiment: Customer sentiment
            
        Returns:
            True if produced successfully
        """
        message = KafkaMessage(
            message_id=str(uuid.uuid4()),
            customer_id=customer_id,
            conversation_id=conversation_id,
            channel=channel,
            message_type='escalation',
            payload={
                'reason': reason,
                'tier': tier,
                'sentiment': sentiment,
            },
            timestamp=datetime.utcnow().isoformat(),
            metadata={'escalation_tier': tier}
        )
        return self.produce_message(TOPIC_ESCALATIONS, message)
    
    def produce_ticket(self, customer_id: str, channel: str, subject: str, 
                      description: str, priority: str = 'P3') -> bool:
        """
        Produce ticket creation event
        
        Args:
            customer_id: Customer ID
            channel: Message channel
            subject: Ticket subject
            description: Ticket description
            priority: Priority level (P1, P2, P3)
            
        Returns:
            True if produced successfully
        """
        message = KafkaMessage(
            message_id=str(uuid.uuid4()),
            customer_id=customer_id,
            conversation_id=str(uuid.uuid4()),  # New conversation for ticket
            channel=channel,
            message_type='ticket',
            payload={
                'subject': subject,
                'description': description,
                'priority': priority,
            },
            timestamp=datetime.utcnow().isoformat(),
            metadata={'priority': priority}
        )
        return self.produce_message(TOPIC_TICKETS, message)
    
    def flush(self, timeout: int = 10):
        """
        Flush producer queue
        
        Args:
            timeout: Timeout in seconds
        """
        try:
            if self.kafka_available:
                remaining = self.producer.flush(timeout)
                if remaining > 0:
                    logger.warning(f"{remaining} messages remained in producer queue after flush")
            else:
                self.producer.flush(timeout)
            logger.info("Producer flushed")
        except Exception as e:
            logger.error(f"Error flushing producer: {e}")


# ============================================================================
# NOVA KAFKA CONSUMER
# ============================================================================

class NovaDeskConsumer:
    """Kafka consumer for NovaDeskAI with error handling"""
    
    def __init__(self, topics: List[str], group_id: str, 
                 bootstrap_servers: str = 'localhost:9092',
                 auto_offset_reset: str = 'earliest'):
        """
        Initialize Kafka consumer
        
        Args:
            topics: List of topics to consume
            group_id: Consumer group ID
            bootstrap_servers: Kafka broker addresses
            auto_offset_reset: Offset reset policy
        """
        self.topics = topics
        self.group_id = group_id
        self.bootstrap_servers = bootstrap_servers
        self.running = False
        self.kafka_available = KAFKA_AVAILABLE
        self.dlq_producer = None  # Will be set if needed
        
        if self.kafka_available:
            try:
                config = {
                    'bootstrap.servers': bootstrap_servers,
                    'group.id': group_id,
                    'auto.offset.reset': auto_offset_reset,
                    'enable.auto.commit': True,
                    'auto.commit.interval.ms': 1000,
                    'session.timeout.ms': 10000,
                    'max.poll.interval.ms': 300000,
                }
                self.consumer = Consumer(config)
                self.consumer.subscribe(topics)
                logger.info(f"NovaDeskConsumer initialized - group: {group_id}, topics: {topics}")
            except Exception as e:
                logger.warning(f"Failed to initialize real Kafka consumer: {e}. Using mock.")
                self.consumer = MockConsumer(topics, group_id, bootstrap_servers, auto_offset_reset)
                self.kafka_available = False
        else:
            self.consumer = MockConsumer(topics, group_id, bootstrap_servers, auto_offset_reset)
    
    def _deserialize(self, raw_value: bytes) -> Optional[KafkaMessage]:
        """
        Deserialize Kafka message bytes to KafkaMessage
        
        Args:
            raw_value: Raw message bytes
            
        Returns:
            KafkaMessage or None if deserialization failed
        """
        try:
            json_str = raw_value.decode('utf-8')
            return KafkaMessage.from_json(json_str)
        except Exception as e:
            logger.error(f"Failed to deserialize message: {e}")
            return None
    
    def _handle_error(self, message: KafkaMessage, error: Exception):
        """
        Handle message processing error - send to DLQ
        
        Args:
            message: KafkaMessage that failed
            error: Exception that occurred
        """
        message.retry_count += 1
        
        if message.retry_count >= message.max_retries:
            logger.error(f"Message {message.message_id} exceeded max retries. Sending to DLQ.")
            
            # Send to DLQ if producer available
            if self.dlq_producer:
                dlq_message = KafkaMessage(
                    message_id=message.message_id,
                    customer_id=message.customer_id,
                    conversation_id=message.conversation_id,
                    channel=message.channel,
                    message_type='dlq',
                    payload={
                        'original_message': message.to_dict(),
                        'error': str(error),
                        'retry_count': message.retry_count,
                    },
                    timestamp=datetime.utcnow().isoformat(),
                    metadata=message.metadata
                )
                self.dlq_producer.produce_message(TOPIC_DLQ, dlq_message)
        else:
            logger.warning(f"Message {message.message_id} failed (retry {message.retry_count}/{message.max_retries}): {error}")
    
    def start(self, message_handler: Callable[[KafkaMessage], None], 
              dlq_producer: Optional[NovaDeskProducer] = None):
        """
        Start consuming messages in a background thread
        
        Args:
            message_handler: Callable that processes KafkaMessage
            dlq_producer: Optional producer for dead letter queue
        """
        self.dlq_producer = dlq_producer
        self.running = True
        
        consumer_thread = threading.Thread(
            target=self._consume_loop,
            args=(message_handler,),
            daemon=True,
            name=f"KafkaConsumer-{self.group_id}"
        )
        consumer_thread.start()
        logger.info(f"Consumer thread started: {consumer_thread.name}")
        
        return consumer_thread
    
    def _consume_loop(self, message_handler: Callable[[KafkaMessage], None]):
        """
        Main consumer loop (runs in background thread)
        
        Args:
            message_handler: Callable that processes KafkaMessage
        """
        while self.running:
            try:
                msg = self.consumer.poll(timeout_ms=1000)
                
                if msg is None:
                    continue
                
                # Check for errors
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        logger.debug(f"Reached end of partition: {msg.topic()}")
                    else:
                        logger.error(f"Kafka error: {msg.error()}")
                    continue
                
                # Deserialize message
                kafka_msg = self._deserialize(msg.value())
                if kafka_msg is None:
                    logger.warning(f"Failed to deserialize message from {msg.topic()}")
                    continue
                
                # Process message
                try:
                    logger.debug(f"Processing message {kafka_msg.message_id} from {msg.topic()}")
                    message_handler(kafka_msg)
                except Exception as e:
                    self._handle_error(kafka_msg, e)
            
            except Exception as e:
                logger.error(f"Consumer loop error: {e}")
                time.sleep(1)  # Back off before retrying
        
        logger.info("Consumer loop stopped")
    
    def stop(self):
        """Gracefully stop consumer"""
        logger.info(f"Stopping consumer: {self.group_id}")
        self.running = False
        try:
            self.consumer.close()
        except Exception as e:
            logger.error(f"Error closing consumer: {e}")


# ============================================================================
# AGENT MESSAGE PROCESSOR
# ============================================================================

class AgentMessageProcessor:
    """Processes Kafka messages through the agent loop"""
    
    def __init__(self, agent_loop, producer: NovaDeskProducer):
        """
        Initialize processor
        
        Args:
            agent_loop: AgentLoop instance from prototype.py
            producer: NovaDeskProducer instance
        """
        self.agent_loop = agent_loop
        self.producer = producer
        self.logger = logging.getLogger(__name__)
    
    def process(self, kafka_message: KafkaMessage) -> None:
        """
        Main message handler - processes inbound message through agent
        
        Args:
            kafka_message: KafkaMessage to process
        """
        start_time = time.time()
        
        try:
            # Extract fields
            message = kafka_message.payload.get('raw_message', '')
            channel = kafka_message.channel
            customer_id = kafka_message.customer_id
            conversation_id = kafka_message.conversation_id
            
            self.logger.info(
                f"Processing message {kafka_message.message_id} - "
                f"customer: {customer_id}, channel: {channel}"
            )
            
            # Process through agent
            agent_result = self.agent_loop.process_message(
                message=message,
                channel=channel,
                customer_id=customer_id,
                conversation_id=conversation_id
            )
            
            # Produce processed result
            self.producer.produce_processed(kafka_message, agent_result)
            self.logger.debug(f"Produced processed result for {kafka_message.message_id}")
            
            # If escalated, produce escalation event
            if agent_result.get('escalated'):
                escalation_details = agent_result.get('escalation_details', {})
                self.producer.produce_escalation(
                    customer_id=customer_id,
                    conversation_id=conversation_id,
                    channel=channel,
                    reason=escalation_details.get('reason', 'Unknown'),
                    tier=escalation_details.get('tier', 2),
                    sentiment=agent_result.get('sentiment', 'neutral')
                )
                self.logger.info(f"Escalation produced for {kafka_message.message_id}")
            
            # Log pipeline timing
            elapsed = time.time() - start_time
            self.logger.info(
                f"Message {kafka_message.message_id} processed in {elapsed:.2f}s - "
                f"escalated: {agent_result.get('escalated')}, "
                f"sentiment: {agent_result.get('sentiment')}"
            )
        
        except Exception as e:
            elapsed = time.time() - start_time
            self.logger.error(
                f"Error processing message {kafka_message.message_id} "
                f"(elapsed: {elapsed:.2f}s): {e}",
                exc_info=True
            )
            raise
    
    def handle_inbound(self, kafka_message: KafkaMessage) -> None:
        """
        Alias for process - used as consumer handler
        
        Args:
            kafka_message: KafkaMessage to process
        """
        self.process(kafka_message)


# ============================================================================
# KAFKA HEALTH CHECKER
# ============================================================================

class KafkaHealthChecker:
    """Checks Kafka broker health"""
    
    @staticmethod
    def check(bootstrap_servers: str = 'localhost:9092') -> Dict[str, Any]:
        """
        Check Kafka broker health
        
        Args:
            bootstrap_servers: Kafka broker addresses
            
        Returns:
            {
                'healthy': bool,
                'broker': str,
                'latency_ms': float or None,
                'error': str or None
            }
        """
        start_time = time.time()
        
        try:
            if not KAFKA_AVAILABLE:
                return {
                    'healthy': False,
                    'broker': bootstrap_servers,
                    'latency_ms': None,
                    'error': 'confluent-kafka not installed'
                }
            
            admin_client = AdminClient({
                'bootstrap.servers': bootstrap_servers,
                'client.id': f'nova-health-check-{uuid.uuid4().hex[:8]}',
                'socket.timeout.ms': 5000,
            })
            
            # Try to get cluster metadata
            cluster_metadata = admin_client.list_topics(timeout=5)
            latency_ms = (time.time() - start_time) * 1000
            
            logger.info(f"Kafka health check OK - {bootstrap_servers} ({latency_ms:.2f}ms)")
            
            return {
                'healthy': True,
                'broker': bootstrap_servers,
                'latency_ms': round(latency_ms, 2),
                'error': None
            }
        
        except Exception as e:
            latency_ms = (time.time() - start_time) * 1000 if start_time else None
            error_msg = str(e)
            
            logger.warning(f"Kafka health check failed - {bootstrap_servers}: {error_msg}")
            
            return {
                'healthy': False,
                'broker': bootstrap_servers,
                'latency_ms': round(latency_ms, 2) if latency_ms else None,
                'error': error_msg
            }


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

def create_producer(bootstrap_servers: str = 'localhost:9092') -> NovaDeskProducer:
    """
    Create a producer instance
    
    Args:
        bootstrap_servers: Kafka broker addresses
        
    Returns:
        NovaDeskProducer instance
    """
    return NovaDeskProducer(bootstrap_servers)


def create_consumer(topics: List[str], group_id: str, 
                   bootstrap_servers: str = 'localhost:9092') -> NovaDeskConsumer:
    """
    Create a consumer instance
    
    Args:
        topics: List of topics to consume
        group_id: Consumer group ID
        bootstrap_servers: Kafka broker addresses
        
    Returns:
        NovaDeskConsumer instance
    """
    return NovaDeskConsumer(topics, group_id, bootstrap_servers)


def start_agent_consumer(agent_loop, producer: NovaDeskProducer, 
                        bootstrap_servers: str = 'localhost:9092') -> Tuple[NovaDeskConsumer, threading.Thread]:
    """
    Create and start an agent message consumer
    
    Args:
        agent_loop: AgentLoop instance
        producer: NovaDeskProducer instance for producing results
        bootstrap_servers: Kafka broker addresses
        
    Returns:
        Tuple of (NovaDeskConsumer, consumer_thread)
    """
    # Create consumer for inbound messages
    consumer = create_consumer(
        topics=[TOPIC_INBOUND],
        group_id=default_config.consumer_group_id,
        bootstrap_servers=bootstrap_servers
    )
    
    # Create processor
    processor = AgentMessageProcessor(agent_loop, producer)
    
    # Start consumer in background thread
    consumer_thread = consumer.start(
        message_handler=processor.handle_inbound,
        dlq_producer=producer
    )
    
    return consumer, consumer_thread


# ============================================================================
# MAIN & DEMONSTRATION
# ============================================================================

if __name__ == '__main__':
    """
    Demonstration of Kafka broker functionality
    """
    print("=" * 80)
    print("NovaDeskAI - Kafka Async Message Streaming Layer")
    print("=" * 80)
    print()
    
    # 1. Health check
    print("1. HEALTH CHECK")
    print("-" * 80)
    health = KafkaHealthChecker.check(default_config.bootstrap_servers)
    print(f"Broker: {health['broker']}")
    print(f"Healthy: {health['healthy']}")
    if health['latency_ms']:
        print(f"Latency: {health['latency_ms']}ms")
    if health['error']:
        print(f"Error: {health['error']}")
    print()
    
    # 2. Create producer
    print("2. PRODUCER INITIALIZATION")
    print("-" * 80)
    producer = create_producer(default_config.bootstrap_servers)
    print("Producer created successfully")
    print()
    
    # 3. Produce sample messages
    print("3. PRODUCING SAMPLE MESSAGES")
    print("-" * 80)
    
    sample_messages = [
        {
            'customer_id': 'cust_001',
            'conversation_id': str(uuid.uuid4()),
            'channel': 'email',
            'raw_message': 'Hi, I forgot my password and can\'t log in. Can you help?',
            'metadata': {'sender': 'john.doe@example.com'}
        },
        {
            'customer_id': 'cust_002',
            'conversation_id': str(uuid.uuid4()),
            'channel': 'whatsapp',
            'raw_message': 'hey, whats the pricing? 😊',
            'metadata': {'phone': '+1234567890'}
        },
        {
            'customer_id': 'cust_003',
            'conversation_id': str(uuid.uuid4()),
            'channel': 'web',
            'raw_message': 'I have a billing question about my invoice.',
            'metadata': {'ip': '192.168.1.1'}
        }
    ]
    
    for i, sample in enumerate(sample_messages, 1):
        success = producer.produce_inbound(
            customer_id=sample['customer_id'],
            conversation_id=sample['conversation_id'],
            channel=sample['channel'],
            raw_message=sample['raw_message'],
            metadata=sample['metadata']
        )
        status = "✓ SUCCESS" if success else "✗ FAILED"
        print(f"{i}. {sample['channel'].upper():8} {status} - {sample['raw_message'][:50]}...")
    
    print()
    
    # 4. Flush producer
    print("4. FLUSHING PRODUCER")
    print("-" * 80)
    producer.flush(timeout=10)
    print("Producer queue flushed")
    print()
    
    # 5. Show consumer setup (don't actually block)
    print("5. CONSUMER SETUP (example)")
    print("-" * 80)
    print("To start consuming messages from TOPIC_INBOUND:")
    print()
    print("```python")
    print("from prototype import AgentLoop")
    print("from kafka_broker import start_agent_consumer")
    print()
    print("agent_loop = AgentLoop()")
    print("producer = create_producer()")
    print()
    print("consumer, thread = start_agent_consumer(agent_loop, producer)")
    print("print(f'Consumer started in thread: {thread.name}')")
    print()
    print("# Messages are now being processed asynchronously")
    print("# Press Ctrl+C to stop consumer when ready")
    print("```")
    print()
    
    print("=" * 80)
    print("Demonstration complete!")
    print("=" * 80)

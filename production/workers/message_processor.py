"""
Message Processor Worker for NovaDeskAI.
Consumes from Kafka topic 'nova.messages.inbound'
Runs the agent and produces results to 'nova.messages.processed'
"""
import asyncio
import json
import logging
import os
import signal
import time
from datetime import datetime, timezone
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("nova.worker.message_processor")

# Try to import Kafka
try:
    from confluent_kafka import Consumer, Producer, KafkaError
    KAFKA_AVAILABLE = True
except ImportError:
    logger.warning("confluent_kafka not installed. Running in demo mode.")
    KAFKA_AVAILABLE = False


class MessageProcessorWorker:
    """Worker for processing messages through the agent."""
    
    TOPIC_INBOUND = 'nova.messages.inbound'
    TOPIC_PROCESSED = 'nova.messages.processed'
    
    def __init__(self, bootstrap_servers: str = 'localhost:9092'):
        """Initialize message processor worker."""
        self.bootstrap_servers = bootstrap_servers
        self.kafka_available = KAFKA_AVAILABLE
        self.running = False
        self.consumer = None
        self.producer = None
        
        if self.kafka_available:
            try:
                self._init_kafka()
                logger.info("Kafka configured successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Kafka: {e}")
                self.kafka_available = False
        else:
            logger.info("Running in demo mode (no Kafka)")
    
    def _init_kafka(self):
        """Initialize Kafka consumer and producer."""
        if not KAFKA_AVAILABLE:
            return
        
        # Consumer configuration
        conf = {
            'bootstrap.servers': self.bootstrap_servers,
            'group.id': 'nova-message-processor',
            'auto.offset.reset': 'earliest'
        }
        self.consumer = Consumer(conf)
        self.consumer.subscribe([self.TOPIC_INBOUND])
        
        # Producer configuration
        prod_conf = {
            'bootstrap.servers': self.bootstrap_servers
        }
        self.producer = Producer(prod_conf)
    
    async def process_message(self, message_data: dict) -> dict:
        """
        Process a message through the agent.
        
        Args:
            message_data: Message in standard format
        
        Returns:
            Processed result with agent response
        """
        try:
            start_time = time.time()
            
            # Extract message components
            content = message_data.get('content', '')
            channel = message_data.get('channel', 'web_form')
            customer_email = message_data.get('customer_email', 'unknown@example.com')
            customer_name = message_data.get('customer_name', 'Customer')
            
            logger.info(f"Processing message from {customer_email} on {channel}")
            
            # Simulate agent processing (in real implementation, call actual agent)
            # For now, return a mock response
            response = {
                'channel': channel,
                'customer_email': customer_email,
                'customer_name': customer_name,
                'original_message': content,
                'agent_response': f"Thank you for your message, {customer_name}. We have received your request and will get back to you shortly.",
                'processed_at': datetime.now(timezone.utc).isoformat(),
                'processing_time_ms': int((time.time() - start_time) * 1000),
                'status': 'processed'
            }
            
            return response
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'original_message': message_data
            }
    
    async def start(self):
        """Start consuming messages from Kafka."""
        if not self.kafka_available or not self.consumer:
            logger.info("Kafka not available. Skipping Kafka consumer startup.")
            return
        
        self.running = True
        logger.info(f"Starting message processor. Consuming from {self.TOPIC_INBOUND}")
        
        try:
            while self.running:
                msg = self.consumer.poll(timeout=1.0)
                
                if msg is None:
                    continue
                
                if msg.error():
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error(f"Kafka error: {msg.error()}")
                        break
                
                # Process the message
                try:
                    message_data = json.loads(msg.value().decode('utf-8'))
                    result = await self.process_message(message_data)
                    
                    # Produce result to output topic
                    if self.producer:
                        self.producer.produce(
                            self.TOPIC_PROCESSED,
                            json.dumps(result).encode('utf-8')
                        )
                        self.producer.flush()
                    
                    logger.info(f"Processed message successfully")
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to decode message: {e}")
                except Exception as e:
                    logger.error(f"Error processing message: {e}")
        except KeyboardInterrupt:
            logger.info("Shutting down message processor")
        finally:
            await self.stop()
    
    async def stop(self):
        """Graceful shutdown."""
        self.running = False
        
        if self.consumer:
            self.consumer.close()
        if self.producer:
            self.producer.flush()
        
        logger.info("Message processor stopped")
    
    async def run_demo(self):
        """Run demo mode with test messages (no Kafka required)."""
        logger.info("Running message processor in demo mode")
        
        # Test messages
        test_messages = [
            {
                'channel': 'email',
                'customer_email': 'alice@example.com',
                'customer_name': 'Alice',
                'content': 'How do I reset my password?'
            },
            {
                'channel': 'whatsapp',
                'customer_email': 'bob@example.com',
                'customer_name': 'Bob',
                'content': 'I have an issue with my account'
            },
            {
                'channel': 'web_form',
                'customer_email': 'charlie@example.com',
                'customer_name': 'Charlie',
                'content': 'Can you help me with billing?'
            }
        ]
        
        logger.info(f"Processing {len(test_messages)} demo messages")
        
        for msg in test_messages:
            result = await self.process_message(msg)
            logger.info(f"Demo result: {json.dumps(result, indent=2)}")
            await asyncio.sleep(0.5)


async def main():
    """Main entry point for message processor."""
    bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092')
    worker = MessageProcessorWorker(bootstrap_servers=bootstrap_servers)
    
    # Handle signals for graceful shutdown
    def signal_handler(sig, frame):
        logger.info("Received shutdown signal")
        asyncio.create_task(worker.stop())
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Run demo or start Kafka consumer
    if worker.kafka_available:
        await worker.start()
    else:
        await worker.run_demo()


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(main())

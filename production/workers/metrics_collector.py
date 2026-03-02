"""
Metrics Collector for NovaDeskAI.
Collects and aggregates performance metrics.
"""
import asyncio
import logging
import os
import time
from collections import defaultdict
from datetime import datetime, timezone
from dataclasses import dataclass, field
from typing import Dict, List, Optional
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger("nova.worker.metrics_collector")


@dataclass
class MetricEvent:
    """A single metric event."""
    name: str
    value: float
    channel: Optional[str] = None
    dimensions: Dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class MetricsCollector:
    """Collector for performance metrics."""
    
    def __init__(self):
        """Initialize metrics collector."""
        # In-memory storage
        self.response_times: List[float] = []
        self.sentiment_counts: Dict[str, int] = defaultdict(int)
        self.escalation_count: int = 0
        self.ticket_count: int = 0
        self.channel_counts: Dict[str, int] = defaultdict(int)
        self.csat_scores: List[float] = []
        self.deflection_count: int = 0
        
        # All events for detailed analysis
        self.all_events: List[MetricEvent] = []
        
        logger.info("Metrics collector initialized")
    
    def record(self, metric_name: str, value: float, channel: Optional[str] = None, dimensions: Dict = None):
        """Record a generic metric."""
        if dimensions is None:
            dimensions = {}
        
        event = MetricEvent(
            name=metric_name,
            value=value,
            channel=channel,
            dimensions=dimensions
        )
        
        self.all_events.append(event)
        logger.debug(f"Recorded metric: {metric_name} = {value}")
    
    def record_response_time(self, latency_ms: float, channel: str):
        """Record response time metric."""
        self.response_times.append(latency_ms)
        self.record('response_time_ms', latency_ms, channel=channel)
    
    def record_sentiment(self, sentiment: str, channel: str):
        """Record sentiment metric."""
        self.sentiment_counts[sentiment] += 1
        sentiment_value = {'positive': 1.0, 'neutral': 0.5, 'negative': 0.0}.get(sentiment, 0.5)
        self.record('sentiment', sentiment_value, channel=channel, dimensions={'sentiment_type': sentiment})
    
    def record_escalation(self, reason: str, tier: str = 'tier1', channel: str = None):
        """Record escalation metric."""
        self.escalation_count += 1
        self.record('escalation', 1.0, channel=channel, dimensions={'reason': reason, 'tier': tier})
    
    def record_ticket_created(self, channel: str, priority: str = 'medium'):
        """Record ticket creation metric."""
        self.ticket_count += 1
        self.channel_counts[channel] += 1
        self.record('ticket_created', 1.0, channel=channel, dimensions={'priority': priority})
    
    def record_csat(self, score: float, channel: str):
        """Record CSAT score."""
        if 0 <= score <= 5:
            self.csat_scores.append(score)
            self.record('csat', score, channel=channel)
    
    def record_deflection(self, channel: str):
        """Record deflection (issue resolved without escalation)."""
        self.deflection_count += 1
        self.record('deflection', 1.0, channel=channel)
    
    def get_summary(self) -> dict:
        """Get summary statistics of collected metrics."""
        # Calculate response time stats
        avg_response_time = 0
        p95_response_time = 0
        if self.response_times:
            avg_response_time = sum(self.response_times) / len(self.response_times)
            sorted_times = sorted(self.response_times)
            p95_index = int(len(sorted_times) * 0.95)
            p95_response_time = sorted_times[p95_index] if p95_index < len(sorted_times) else sorted_times[-1]
        
        # Calculate sentiment breakdown
        total_sentiment = sum(self.sentiment_counts.values())
        sentiment_breakdown = {}
        if total_sentiment > 0:
            for sentiment, count in self.sentiment_counts.items():
                sentiment_breakdown[sentiment] = {
                    'count': count,
                    'percentage': (count / total_sentiment) * 100
                }
        
        # Calculate escalation rate
        escalation_rate = 0
        total_interactions = self.ticket_count + self.deflection_count
        if total_interactions > 0:
            escalation_rate = (self.escalation_count / total_interactions) * 100
        
        # Calculate CSAT average
        csat_avg = 0
        if self.csat_scores:
            csat_avg = sum(self.csat_scores) / len(self.csat_scores)
        
        # Calculate deflection rate
        deflection_rate = 0
        if total_interactions > 0:
            deflection_rate = (self.deflection_count / total_interactions) * 100
        
        return {
            'avg_response_time_ms': round(avg_response_time, 2),
            'p95_response_time_ms': round(p95_response_time, 2),
            'sentiment_breakdown': sentiment_breakdown,
            'escalation_rate_percent': round(escalation_rate, 2),
            'ticket_count': self.ticket_count,
            'escalation_count': self.escalation_count,
            'deflection_count': self.deflection_count,
            'deflection_rate_percent': round(deflection_rate, 2),
            'csat_avg': round(csat_avg, 2),
            'channel_breakdown': dict(self.channel_counts),
            'total_metrics_recorded': len(self.all_events)
        }
    
    async def flush_to_db(self):
        """Write metrics to database if available."""
        try:
            # Import database module
            from production.database import queries
            
            logger.info(f"Flushing {len(self.all_events)} metrics to database")
            
            # Write each metric to database
            for event in self.all_events:
                await queries.record_metric(
                    metric_name=event.name,
                    metric_value=event.value,
                    channel=event.channel,
                    dimensions=event.dimensions
                )
            
            logger.info("Metrics flushed to database successfully")
        except ImportError:
            logger.warning("Database module not available. Skipping flush.")
        except Exception as e:
            logger.error(f"Failed to flush metrics to database: {e}")
    
    async def start_background_flush(self, interval_seconds: int = 60):
        """Start periodic background flush of metrics."""
        logger.info(f"Starting background metrics flush (interval: {interval_seconds}s)")
        
        try:
            while True:
                await asyncio.sleep(interval_seconds)
                
                # Get summary before flush
                summary = self.get_summary()
                logger.info(f"Metrics summary: {summary}")
                
                # Flush to database
                await self.flush_to_db()
        except asyncio.CancelledError:
            logger.info("Background flush cancelled")
        except Exception as e:
            logger.error(f"Error in background flush: {e}")


# Module-level singleton instance
metrics = MetricsCollector()


async def demo():
    """Demo metrics collection."""
    logger.info("Running metrics collector demo")
    
    # Simulate some metrics
    metrics.record_response_time(150.5, channel='email')
    metrics.record_response_time(85.2, channel='whatsapp')
    metrics.record_response_time(200.1, channel='web_form')
    
    metrics.record_sentiment('positive', channel='email')
    metrics.record_sentiment('positive', channel='whatsapp')
    metrics.record_sentiment('neutral', channel='web_form')
    
    metrics.record_ticket_created(channel='email', priority='medium')
    metrics.record_ticket_created(channel='whatsapp', priority='high')
    metrics.record_ticket_created(channel='web_form', priority='low')
    
    metrics.record_escalation(reason='pricing_inquiry', tier='tier2', channel='email')
    metrics.record_deflection(channel='whatsapp')
    metrics.record_deflection(channel='web_form')
    
    metrics.record_csat(score=4.5, channel='email')
    metrics.record_csat(score=5.0, channel='whatsapp')
    metrics.record_csat(score=3.8, channel='web_form')
    
    # Print summary
    summary = metrics.get_summary()
    import json
    logger.info(f"Metrics Summary:\n{json.dumps(summary, indent=2)}")


if __name__ == '__main__':
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    asyncio.run(demo())

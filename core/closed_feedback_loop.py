"""
==========================================================
JARVIS - Closed Feedback Loop (Bridge)
==========================================================
Connects Distributed Tracing and Self-Monitoring to 
Self-Evolving Architecture. Closes the loop: 
Senses (Tracing) -> Analysis (Monitor) -> Action (SEA)
==========================================================
"""

import logging
import asyncio
from typing import Dict, Any, List
from .distributed_tracing import tracer, Trace, Span, suppress_tracing
from .self_monitor import SelfMonitor, MetricType
from .self_evolving_architecture import SEAController, Bottleneck, PerformanceSample

logger = logging.getLogger(__name__)

class ClosedFeedbackLoop:
    """
    The "Central Nervous System" bridge.
    Automatically reacts to performance data.
    """
    
    def __init__(self, monitor: SelfMonitor, sea: SEAController):
        self.monitor = monitor
        self.sea = sea
        self.is_running = False
        self._processed_traces = set()

    async def start(self):
        """Start the feedback loop"""
        self.is_running = True
        logger.info("🔗 Closed Feedback Loop active")
        asyncio.create_task(self._process_loop())

    async def _process_loop(self):
        while self.is_running:
            # 1. Pull completed traces from Tracer
            for trace_id, trace in list(tracer.traces.items()):
                if trace.end_time and trace_id not in self._processed_traces:
                    await self._analyze_trace(trace)
                    self._processed_traces.add(trace_id)
            
            # Keep set size reasonable
            if len(self._processed_traces) > 1000:
                self._processed_traces.clear()
                
            await asyncio.sleep(5)

    @suppress_tracing
    async def _analyze_trace(self, trace: Trace):
        """Analyze trace and trigger responses with recursion guard"""
        # Record success/failure in Monitor
        trace_status = "ok"
        error_msg = None
        
        for span in trace.spans:
            if span.status == "error":
                trace_status = "error"
                error_msg = span.error_message
                break
        
        self.monitor.record_action(
            action=f"Trace:{trace.trace_id}",
            action_type="system_flow",
            success=(trace_status == "ok"),
            duration=trace.total_duration_ms / 1000.0,
            error=error_msg
        )

        # If bottlenecks found, feed directly to SEA
        bottlenecks = trace.get_bottlenecks(threshold_ms=200)
        for b in bottlenecks:
            logger.warning(f"⚠️ Bottleneck detected in {b.name}: {b.duration_ms}ms")
            
            # Convert Span to SEA Bottleneck
            sample = PerformanceSample(
                function_signature=b.name,
                execution_time=b.duration_ms / 1000.0,
                memory_usage=0.0, # Tracer doesn't track mem yet
                cpu_utilization=0.0,
                io_wait_time=0.0,
                timestamp=b.start_time
            )
            
            sea_bottleneck = Bottleneck(
                function_signature=b.name,
                performance_sample=sample,
                severity=min(1.0, b.duration_ms / 1000.0),
                suggested_strategies=[] # SEA will determine
            )
            
            # Push to SEA DNA
            self.sea.dna.record_sample(sample)
            
            # If health score is low, trigger immediate evolution check
            if self.monitor._calculate_health_score() < 70:
                logger.info(f"🚀 Low health ({self.monitor._calculate_health_score()}). Triggering SEA check.")
                # SEA controller loop will pick this up on next iteration

feedback_loop = None

def initialize_feedback(monitor, sea):
    global feedback_loop
    feedback_loop = ClosedFeedbackLoop(monitor, sea)
    return feedback_loop

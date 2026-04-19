"""
==========================================================
JARVIS - PhD-Level Distributed Tracing System
==========================================================
OpenTelemetry-compatible tracing for Node.js → gRPC → Python
Tracks message flow, latency, and bottlenecks across services

Features:
- Trace context propagation
- Span hierarchy
- Performance metrics
- Bottleneck detection
- Export to Jaeger/Zipkin
==========================================================
"""

import time
import uuid
import json
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import threading

logger = logging.getLogger(__name__)


class SpanKind(Enum):
    """Span types"""
    SERVER = "server"
    CLIENT = "client"
    INTERNAL = "internal"
    PRODUCER = "producer"
    CONSUMER = "consumer"


@dataclass
class Span:
    """Distributed tracing span"""
    trace_id: str
    span_id: str
    parent_span_id: Optional[str]
    name: str
    kind: SpanKind
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    attributes: Dict[str, Any] = field(default_factory=dict)
    events: List[Dict[str, Any]] = field(default_factory=list)
    status: str = "ok"  # ok, error
    error_message: Optional[str] = None

    def end(self):
        """End the span"""
        self.end_time = time.time()
        self.duration_ms = (self.end_time - self.start_time) * 1000

    def add_event(self, name: str, attributes: Dict[str, Any] = None):
        """Add event to span"""
        self.events.append({
            "name": name,
            "timestamp": time.time(),
            "attributes": attributes or {}
        })

    def set_attribute(self, key: str, value: Any):
        """Set span attribute"""
        self.attributes[key] = value

    def set_error(self, error: Exception):
        """Mark span as error"""
        self.status = "error"
        self.error_message = str(error)
        self.attributes["error.type"] = type(error).__name__
        self.attributes["error.message"] = str(error)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "trace_id": self.trace_id,
            "span_id": self.span_id,
            "parent_span_id": self.parent_span_id,
            "name": self.name,
            "kind": self.kind.value,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration_ms": self.duration_ms,
            "attributes": self.attributes,
            "events": self.events,
            "status": self.status,
            "error_message": self.error_message
        }


@dataclass
class Trace:
    """Complete trace with all spans"""
    trace_id: str
    spans: List[Span] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    total_duration_ms: Optional[float] = None

    def add_span(self, span: Span):
        """Add span to trace"""
        self.spans.append(span)

    def end(self):
        """End the trace"""
        self.end_time = time.time()
        self.total_duration_ms = (self.end_time - self.start_time) * 1000

    def get_critical_path(self) -> List[Span]:
        """Get critical path (longest chain)"""
        # Build span tree
        span_map = {s.span_id: s for s in self.spans}

        def get_path_duration(span: Span) -> float:
            """Get total duration of path from this span"""
            children = [s for s in self.spans if s.parent_span_id == span.span_id]
            if not children:
                return span.duration_ms or 0

            max_child_duration = max(get_path_duration(child) for child in children)
            return (span.duration_ms or 0) + max_child_duration

        # Find root spans
        root_spans = [s for s in self.spans if s.parent_span_id is None]

        if not root_spans:
            return []

        # Find critical path
        critical_root = max(root_spans, key=get_path_duration)

        # Build path
        path = [critical_root]
        current = critical_root

        while True:
            children = [s for s in self.spans if s.parent_span_id == current.span_id]
            if not children:
                break
            current = max(children, key=lambda s: s.duration_ms or 0)
            path.append(current)

        return path

    def get_bottlenecks(self, threshold_ms: float = 100) -> List[Span]:
        """Get spans that took longer than threshold"""
        return [s for s in self.spans if (s.duration_ms or 0) > threshold_ms]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "trace_id": self.trace_id,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "total_duration_ms": self.total_duration_ms,
            "spans": [s.to_dict() for s in self.spans],
            "span_count": len(self.spans)
        }


class Tracer:
    """
    PhD-Level Distributed Tracer
    - Context propagation
    - Span management
    - Trace storage
    - Performance analysis
    """

    def __init__(self):
        self.traces: Dict[str, Trace] = {}
        self.active_spans: Dict[str, Span] = {}
        self.max_traces = 1000
        self.lock = threading.Lock()

    def start_trace(self, name: str, trace_id: Optional[str] = None) -> Trace:
        """Start a new trace"""
        trace_id = trace_id or self._generate_id()

        with self.lock:
            trace = Trace(trace_id=trace_id)
            self.traces[trace_id] = trace

            # Trim old traces
            if len(self.traces) > self.max_traces:
                oldest_id = min(self.traces.keys(), key=lambda k: self.traces[k].start_time)
                del self.traces[oldest_id]

        logger.debug(f"Started trace: {trace_id}")
        return trace

    def start_span(
        self,
        name: str,
        trace_id: str,
        parent_span_id: Optional[str] = None,
        kind: SpanKind = SpanKind.INTERNAL,
        attributes: Dict[str, Any] = None
    ) -> Span:
        """Start a new span with recursion guard"""
        if getattr(_tracing_suppressed, 'active', False):
            # Return a dummy span that doesn't record anything
            return Span(trace_id, "dummy", None, "dummy", kind, start_time=time.time())

        span = Span(
            trace_id=trace_id,
            span_id=self._generate_id(),
            parent_span_id=parent_span_id,
            name=name,
            kind=kind,
            start_time=time.time(),
            attributes=attributes or {}
        )

        with self.lock:
            self.active_spans[span.span_id] = span

            if trace_id in self.traces:
                self.traces[trace_id].add_span(span)

        logger.debug(f"Started span: {name} ({span.span_id})")
        return span

    def end_span(self, span: Span):
        """End a span"""
        span.end()

        with self.lock:
            if span.span_id in self.active_spans:
                del self.active_spans[span.span_id]

        logger.debug(f"Ended span: {span.name} ({span.duration_ms:.2f}ms)")

    def end_trace(self, trace_id: str):
        """End a trace"""
        with self.lock:
            if trace_id in self.traces:
                self.traces[trace_id].end()
                logger.info(f"Trace completed: {trace_id} ({self.traces[trace_id].total_duration_ms:.2f}ms)")

    def get_trace(self, trace_id: str) -> Optional[Trace]:
        """Get trace by ID"""
        return self.traces.get(trace_id)

    def get_trace_context(self, trace_id: str, span_id: str) -> Dict[str, str]:
        """Get trace context for propagation"""
        return {
            "traceparent": f"00-{trace_id}-{span_id}-01",
            "trace_id": trace_id,
            "span_id": span_id
        }

    def extract_trace_context(self, headers: Dict[str, str]) -> Optional[Dict[str, str]]:
        """Extract trace context from headers"""
        traceparent = headers.get("traceparent") or headers.get("x-trace-id")

        if traceparent:
            parts = traceparent.split("-")
            if len(parts) >= 3:
                return {
                    "trace_id": parts[1],
                    "parent_span_id": parts[2]
                }

        # Fallback to individual headers
        trace_id = headers.get("trace_id") or headers.get("x-trace-id")
        span_id = headers.get("span_id") or headers.get("x-span-id")

        if trace_id:
            return {
                "trace_id": trace_id,
                "parent_span_id": span_id
            }

        return None

    def analyze_performance(self, trace_id: str) -> Dict[str, Any]:
        """Analyze trace performance"""
        trace = self.get_trace(trace_id)

        if not trace:
            return {"error": "Trace not found"}

        critical_path = trace.get_critical_path()
        bottlenecks = trace.get_bottlenecks(threshold_ms=100)

        # Calculate span statistics
        span_durations = [s.duration_ms for s in trace.spans if s.duration_ms]

        if span_durations:
            avg_duration = sum(span_durations) / len(span_durations)
            max_duration = max(span_durations)
            min_duration = min(span_durations)
        else:
            avg_duration = max_duration = min_duration = 0

        return {
            "trace_id": trace_id,
            "total_duration_ms": trace.total_duration_ms,
            "span_count": len(trace.spans),
            "critical_path": [s.name for s in critical_path],
            "critical_path_duration_ms": sum(s.duration_ms or 0 for s in critical_path),
            "bottlenecks": [{"name": s.name, "duration_ms": s.duration_ms} for s in bottlenecks],
            "statistics": {
                "avg_span_duration_ms": avg_duration,
                "max_span_duration_ms": max_duration,
                "min_span_duration_ms": min_duration
            }
        }

    def export_jaeger(self, trace_id: str) -> Dict[str, Any]:
        """Export trace in Jaeger format"""
        trace = self.get_trace(trace_id)

        if not trace:
            return {"error": "Trace not found"}

        return {
            "traceID": trace_id,
            "spans": [
                {
                    "traceID": trace_id,
                    "spanID": s.span_id,
                    "operationName": s.name,
                    "references": [
                        {"refType": "CHILD_OF", "traceID": trace_id, "spanID": s.parent_span_id}
                    ] if s.parent_span_id else [],
                    "startTime": int(s.start_time * 1000000),  # microseconds
                    "duration": int((s.duration_ms or 0) * 1000),  # microseconds
                    "tags": [{"key": k, "value": v} for k, v in s.attributes.items()],
                    "logs": [
                        {
                            "timestamp": int(e["timestamp"] * 1000000),
                            "fields": [{"key": k, "value": v} for k, v in e["attributes"].items()]
                        }
                        for e in s.events
                    ]
                }
                for s in trace.spans
            ]
        }

    def _generate_id(self) -> str:
        """Generate unique ID"""
        return uuid.uuid4().hex[:16]

    def get_stats(self) -> Dict[str, Any]:
        """Get tracer statistics"""
        with self.lock:
            completed_traces = [t for t in self.traces.values() if t.end_time is not None]

            if completed_traces:
                avg_duration = sum(t.total_duration_ms for t in completed_traces) / len(completed_traces)
                max_duration = max(t.total_duration_ms for t in completed_traces)
            else:
                avg_duration = max_duration = 0

            return {
                "total_traces": len(self.traces),
                "active_spans": len(self.active_spans),
                "completed_traces": len(completed_traces),
                "avg_trace_duration_ms": avg_duration,
                "max_trace_duration_ms": max_duration
            }


# Global tracer instance
tracer = Tracer()

# Recursion Guard for Feedback Loops
_tracing_suppressed = threading.local()

def suppress_tracing(func):
    """Decorator to suppress tracing for a function and its children"""
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            old_val = getattr(_tracing_suppressed, 'active', False)
            _tracing_suppressed.active = True
            try:
                return await func(*args, **kwargs)
            finally:
                _tracing_suppressed.active = old_val
        return async_wrapper
    else:
        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            old_val = getattr(_tracing_suppressed, 'active', False)
            _tracing_suppressed.active = True
            try:
                return func(*args, **kwargs)
            finally:
                _tracing_suppressed.active = old_val
        return sync_wrapper

# Context manager for easy span usage
class traced_span:
    """Context manager for tracing spans"""

    def __init__(self, name: str, trace_id: str, parent_span_id: Optional[str] = None,
                 kind: SpanKind = SpanKind.INTERNAL, attributes: Dict[str, Any] = None):
        self.name = name
        self.trace_id = trace_id
        self.parent_span_id = parent_span_id
        self.kind = kind
        self.attributes = attributes
        self.span: Optional[Span] = None

    def __enter__(self) -> Span:
        self.span = tracer.start_span(
            self.name,
            self.trace_id,
            self.parent_span_id,
            self.kind,
            self.attributes
        )
        return self.span

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            self.span.set_error(exc_val)
        tracer.end_span(self.span)


# Test
if __name__ == "__main__":
    # Create a trace
    trace = tracer.start_trace("test_message_flow")

    # Simulate message flow
    with traced_span("whatsapp_receive", trace.trace_id, kind=SpanKind.SERVER) as span1:
        span1.set_attribute("from", "1234567890")
        span1.set_attribute("message", "Hello JARVIS")
        time.sleep(0.01)

        with traced_span("grpc_call", trace.trace_id, span1.span_id, kind=SpanKind.CLIENT) as span2:
            span2.set_attribute("method", "ProcessMessage")
            time.sleep(0.05)

            with traced_span("orchestrator_process", trace.trace_id, span2.span_id) as span3:
                span3.set_attribute("orchestrator", "v11.0")
                time.sleep(0.1)

                with traced_span("llm_call", trace.trace_id, span3.span_id, kind=SpanKind.CLIENT) as span4:
                    span4.set_attribute("model", "llama-3.3-70b")
                    time.sleep(0.2)

    tracer.end_trace(trace.trace_id)

    # Analyze
    analysis = tracer.analyze_performance(trace.trace_id)
    print(json.dumps(analysis, indent=2))

---
source_file: "core\resilience_patterns.py"
type: "rationale"
community: "Community None"
location: "L142"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_None
---

# Decorator for applying circuit breaker pattern

## Connections
- [[Bulkhead]] - `uses` [INFERRED]
- [[CircuitBreaker]] - `uses` [INFERRED]
- [[CircuitMetrics]] - `uses` [INFERRED]
- [[CircuitState]] - `uses` [INFERRED]
- [[ErrorCategory]] - `uses` [INFERRED]
- [[ErrorSeverity]] - `uses` [INFERRED]
- [[JarvisError]] - `uses` [INFERRED]
- [[ResilienceManager]] - `uses` [INFERRED]
- [[ResourcePool]] - `uses` [INFERRED]
- [[Result]] - `uses` [INFERRED]
- [[RetryPolicy]] - `uses` [INFERRED]
- [[WatchdogTimer]] - `uses` [INFERRED]
- [[circuit_breaker()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/Community_None
---
source_file: "core\resilience_patterns.py"
type: "rationale"
community: "Community 12"
location: "L140"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_12
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

#graphify/rationale #graphify/INFERRED #community/Community_12
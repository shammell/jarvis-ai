---
source_file: "core\resilience_patterns.py"
type: "rationale"
community: "Community 12"
location: "L145"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_12
---

# Decorator for applying retry policy

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
- [[retry_policy()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/Community_12
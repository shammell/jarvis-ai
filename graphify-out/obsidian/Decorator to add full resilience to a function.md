---
source_file: "core\error_handling.py"
type: "rationale"
community: "Community 12"
location: "L761"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_12
---

# Decorator to add full resilience to a function

## Connections
- [[Bulkhead]] - `uses` [INFERRED]
- [[CircuitBreaker]] - `uses` [INFERRED]
- [[ResilienceManager]] - `uses` [INFERRED]
- [[ResourcePool]] - `uses` [INFERRED]
- [[RetryPolicy]] - `uses` [INFERRED]
- [[WatchdogTimer]] - `uses` [INFERRED]
- [[with_resilience()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/Community_12
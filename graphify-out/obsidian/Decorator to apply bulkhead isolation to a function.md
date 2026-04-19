---
source_file: "core\error_handling.py"
type: "rationale"
community: "Community 12"
location: "L456"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_12
---

# Decorator to apply bulkhead isolation to a function

## Connections
- [[.bulkhead_protect()]] - `rationale_for` [EXTRACTED]
- [[Bulkhead]] - `uses` [INFERRED]
- [[CircuitBreaker]] - `uses` [INFERRED]
- [[ResilienceManager]] - `uses` [INFERRED]
- [[ResourcePool]] - `uses` [INFERRED]
- [[RetryPolicy]] - `uses` [INFERRED]
- [[WatchdogTimer]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/Community_12
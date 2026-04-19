---
source_file: "core\error_handling.py"
type: "rationale"
community: "Community None"
location: "L751"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_None
---

# Decorator to add bulkhead isolation to a function

## Connections
- [[Bulkhead]] - `uses` [INFERRED]
- [[CircuitBreaker]] - `uses` [INFERRED]
- [[ResilienceManager]] - `uses` [INFERRED]
- [[ResourcePool]] - `uses` [INFERRED]
- [[RetryPolicy]] - `uses` [INFERRED]
- [[WatchdogTimer]] - `uses` [INFERRED]
- [[with_bulkhead()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/Community_None
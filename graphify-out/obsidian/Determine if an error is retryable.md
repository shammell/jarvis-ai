---
source_file: "core\error_handling.py"
type: "rationale"
community: "Community 12"
location: "L564"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_12
---

# Determine if an error is retryable

## Connections
- [[._is_retryable_error()]] - `rationale_for` [EXTRACTED]
- [[Bulkhead]] - `uses` [INFERRED]
- [[CircuitBreaker]] - `uses` [INFERRED]
- [[ResilienceManager]] - `uses` [INFERRED]
- [[ResourcePool]] - `uses` [INFERRED]
- [[RetryPolicy]] - `uses` [INFERRED]
- [[WatchdogTimer]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/Community_12
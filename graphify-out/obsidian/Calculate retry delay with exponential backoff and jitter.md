---
source_file: "core\error_handling.py"
type: "rationale"
community: "Community 12"
location: "L592"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_12
---

# Calculate retry delay with exponential backoff and jitter

## Connections
- [[._calculate_retry_delay()]] - `rationale_for` [EXTRACTED]
- [[Bulkhead]] - `uses` [INFERRED]
- [[CircuitBreaker]] - `uses` [INFERRED]
- [[ResilienceManager]] - `uses` [INFERRED]
- [[ResourcePool]] - `uses` [INFERRED]
- [[RetryPolicy]] - `uses` [INFERRED]
- [[WatchdogTimer]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/Community_12
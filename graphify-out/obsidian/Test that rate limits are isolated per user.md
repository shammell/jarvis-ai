---
source_file: "tests\security\test_rate_limiting.py"
type: "rationale"
community: "Community 3"
location: "L110"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_3
---

# Test that rate limits are isolated per user

## Connections
- [[.test_rate_limit_user_isolation()]] - `rationale_for` [EXTRACTED]
- [[Permission_1]] - `uses` [INFERRED]
- [[SecurityManager_1]] - `uses` [INFERRED]
- [[UserRole_1]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/Community_3
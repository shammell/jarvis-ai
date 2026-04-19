---
source_file: "tests\security\test_rbac.py"
type: "rationale"
community: "Community 3"
location: "L134"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_3
---

# Test that roles don't share unintended permissions

## Connections
- [[.test_permission_isolation()]] - `rationale_for` [EXTRACTED]
- [[Permission_1]] - `uses` [INFERRED]
- [[SecurityManager_1]] - `uses` [INFERRED]
- [[UserRole_1]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/Community_3
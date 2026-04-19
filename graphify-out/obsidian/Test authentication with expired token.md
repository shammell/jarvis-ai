---
source_file: "tests\security\test_security_middleware.py"
type: "rationale"
community: "Community 3"
location: "L74"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_3
---

# Test authentication with expired token

## Connections
- [[.test_authenticate_request_expired_token()]] - `rationale_for` [EXTRACTED]
- [[InputValidator_1]] - `uses` [INFERRED]
- [[Permission_1]] - `uses` [INFERRED]
- [[SecurityManager_1]] - `uses` [INFERRED]
- [[SecurityMiddleware_1]] - `uses` [INFERRED]
- [[UserRole_1]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/Community_3
---
source_file: "core\routing_policy.py"
type: "rationale"
community: "Community 15"
location: "L263"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_15
---

# Check if a task requires human approval.          Args:             task_type: T

## Connections
- [[.requires_approval()]] - `rationale_for` [EXTRACTED]
- [[ProviderCapability]] - `uses` [INFERRED]
- [[ProviderContract]] - `uses` [INFERRED]
- [[ProviderStatus]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/Community_15
---
source_file: "tests\safety\test_action_receipt_store.py"
type: "rationale"
community: "Community 54"
location: "L96"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_54
---

# Receipt store supports lookup and listing.

## Connections
- [[ActionReceiptStore]] - `uses` [INFERRED]
- [[ExecutionReceipt]] - `uses` [INFERRED]
- [[ReceiptStatus]] - `uses` [INFERRED]
- [[TestReceiptRetrieval]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/Community_54
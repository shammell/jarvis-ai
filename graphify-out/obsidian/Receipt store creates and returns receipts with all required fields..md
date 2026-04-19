---
source_file: "tests\safety\test_action_receipt_store.py"
type: "rationale"
community: "Community 54"
location: "L14"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_54
---

# Receipt store creates and returns receipts with all required fields.

## Connections
- [[ActionReceiptStore]] - `uses` [INFERRED]
- [[ExecutionReceipt]] - `uses` [INFERRED]
- [[ReceiptStatus]] - `uses` [INFERRED]
- [[TestReceiptCreation]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/Community_54
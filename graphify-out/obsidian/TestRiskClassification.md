---
source_file: "tests\safety\test_honest_execution_policy.py"
type: "code"
community: "Community 65"
location: "L12"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Community_65
---

# TestRiskClassification

## Connections
- [[.setup_method()_2]] - `method` [EXTRACTED]
- [[.test_blocked_illegal_action_is_denied()]] - `method` [EXTRACTED]
- [[.test_empty_action_is_blocked()]] - `method` [EXTRACTED]
- [[.test_high_risk_deletion_requires_explicit_approval()]] - `method` [EXTRACTED]
- [[.test_low_risk_read_action_is_auto_approved()]] - `method` [EXTRACTED]
- [[.test_medium_risk_file_write_requires_approval()]] - `method` [EXTRACTED]
- [[.test_policy_provides_human_readable_reason()]] - `method` [EXTRACTED]
- [[HonestExecutionPolicy]] - `uses` [INFERRED]
- [[Policy maps actions to correct risk classes with reasons.]] - `rationale_for` [EXTRACTED]
- [[RiskClass]] - `uses` [INFERRED]
- [[test_honest_execution_policy.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Community_65
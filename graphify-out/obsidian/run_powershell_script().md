---
source_file: "tests\integration\test_windows_startup_tasks.py"
type: "code"
community: "Community 26"
location: "L80"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Community_26
---

# run_powershell_script()

## Connections
- [[.run()_10]] - `calls` [INFERRED]
- [[.test_idempotency_install()]] - `calls` [EXTRACTED]
- [[.test_install_creates_task()]] - `calls` [EXTRACTED]
- [[.test_remove_deletes_task()]] - `calls` [EXTRACTED]
- [[Run a PowerShell script and return the result.]] - `rationale_for` [EXTRACTED]
- [[cleanup_task()]] - `calls` [EXTRACTED]
- [[str]] - `calls` [INFERRED]
- [[test_windows_startup_tasks.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Community_26
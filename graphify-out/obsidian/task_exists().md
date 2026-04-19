---
source_file: "tests\integration\test_windows_startup_tasks.py"
type: "code"
community: "Community 26"
location: "L102"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Community_26
---

# task_exists()

## Connections
- [[.run()_10]] - `calls` [INFERRED]
- [[.test_idempotency_install()]] - `calls` [EXTRACTED]
- [[.test_install_creates_task()]] - `calls` [EXTRACTED]
- [[.test_remove_deletes_task()]] - `calls` [EXTRACTED]
- [[Check if a Task Scheduler task exists.]] - `rationale_for` [EXTRACTED]
- [[cleanup_task()]] - `calls` [EXTRACTED]
- [[test_windows_startup_tasks.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Community_26
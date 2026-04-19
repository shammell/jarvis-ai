---
source_file: "voice\voice_bridge.py"
type: "rationale"
community: "Community 11"
location: "L59"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_11
---

# Bridge between voice system and JARVIS orchestrator.      Takes transcribed text

## Connections
- [[HybridLLMManager]] - `uses` [INFERRED]
- [[IntentType]] - `uses` [INFERRED]
- [[PromptGenerator]] - `uses` [INFERRED]
- [[VoiceBridge]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/Community_11
---
source_file: "voice\audio_manager.py"
type: "rationale"
community: "Community 29"
location: "L300"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_29
---

# In continuous mode, keep listening without requiring wake trigger.

## Connections
- [[._continuous_listen_loop()]] - `rationale_for` [EXTRACTED]
- [[STTConfig]] - `uses` [INFERRED]
- [[SpeechToText]] - `uses` [INFERRED]
- [[TTSConfig]] - `uses` [INFERRED]
- [[TextToSpeech]] - `uses` [INFERRED]
- [[WakeConfig]] - `uses` [INFERRED]
- [[WakeDetector]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/Community_29
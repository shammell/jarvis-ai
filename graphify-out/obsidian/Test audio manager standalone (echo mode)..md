---
source_file: "voice\audio_manager.py"
type: "rationale"
community: "Community 29"
location: "L346"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_29
---

# Test audio manager standalone (echo mode).

## Connections
- [[STTConfig]] - `uses` [INFERRED]
- [[SpeechToText]] - `uses` [INFERRED]
- [[TTSConfig]] - `uses` [INFERRED]
- [[TextToSpeech]] - `uses` [INFERRED]
- [[WakeConfig]] - `uses` [INFERRED]
- [[WakeDetector]] - `uses` [INFERRED]
- [[_test()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/Community_29
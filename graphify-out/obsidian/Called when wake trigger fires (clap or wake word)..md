---
source_file: "voice\audio_manager.py"
type: "rationale"
community: "Community 29"
location: "L200"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_29
---

# Called when wake trigger fires (clap or wake word).

## Connections
- [[._on_wake_trigger()]] - `rationale_for` [EXTRACTED]
- [[STTConfig]] - `uses` [INFERRED]
- [[SpeechToText]] - `uses` [INFERRED]
- [[TTSConfig]] - `uses` [INFERRED]
- [[TextToSpeech]] - `uses` [INFERRED]
- [[WakeConfig]] - `uses` [INFERRED]
- [[WakeDetector]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/Community_29
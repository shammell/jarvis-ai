---
source_file: "voice\audio_manager.py"
type: "rationale"
community: "Community 29"
location: "L71"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_29
---

# Play a system beep sound (Windows only).

## Connections
- [[STTConfig]] - `uses` [INFERRED]
- [[SpeechToText]] - `uses` [INFERRED]
- [[TTSConfig]] - `uses` [INFERRED]
- [[TextToSpeech]] - `uses` [INFERRED]
- [[WakeConfig]] - `uses` [INFERRED]
- [[WakeDetector]] - `uses` [INFERRED]
- [[play_beep()]] - `rationale_for` [EXTRACTED]

#graphify/rationale #graphify/INFERRED #community/Community_29
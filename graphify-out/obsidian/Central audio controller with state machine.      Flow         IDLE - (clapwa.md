---
source_file: "voice\audio_manager.py"
type: "rationale"
community: "Community 29"
location: "L137"
tags:
  - graphify/rationale
  - graphify/INFERRED
  - community/Community_29
---

# Central audio controller with state machine.      Flow:         IDLE -> (clap/wa

## Connections
- [[AudioManager]] - `rationale_for` [EXTRACTED]
- [[STTConfig]] - `uses` [INFERRED]
- [[SpeechToText]] - `uses` [INFERRED]
- [[TTSConfig]] - `uses` [INFERRED]
- [[TextToSpeech]] - `uses` [INFERRED]
- [[WakeConfig]] - `uses` [INFERRED]
- [[WakeDetector]] - `uses` [INFERRED]

#graphify/rationale #graphify/INFERRED #community/Community_29
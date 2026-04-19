---
source_file: "voice\wake_detector.py"
type: "code"
community: "Community 29"
location: "L90"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Community_29
---

# WakeDetector

## Connections
- [[.__init__()_202]] - `calls` [INFERRED]
- [[.__init__()_210]] - `method` [EXTRACTED]
- [[._audio_callback()]] - `method` [EXTRACTED]
- [[._detect_clap()]] - `method` [EXTRACTED]
- [[._transcribe_buffer()]] - `method` [EXTRACTED]
- [[._trigger_wake()]] - `method` [EXTRACTED]
- [[._wake_word_loop()]] - `method` [EXTRACTED]
- [[.start()_8]] - `method` [EXTRACTED]
- [[.stop()_6]] - `method` [EXTRACTED]
- [[AudioManager]] - `uses` [INFERRED]
- [[AudioManagerConfig]] - `uses` [INFERRED]
- [[AudioState]] - `uses` [INFERRED]
- [[BeepType]] - `uses` [INFERRED]
- [[Called when wake trigger fires (clap or wake word).]] - `uses` [INFERRED]
- [[Central audio controller with state machine.      Flow         IDLE - (clapwa]] - `uses` [INFERRED]
- [[Detects wake triggers     1. Double-clap (amplitude spike analysis)     2. Wake]] - `rationale_for` [EXTRACTED]
- [[Different beep sounds for different events.]] - `uses` [INFERRED]
- [[Immutable audio manager configuration.]] - `uses` [INFERRED]
- [[In continuous mode, keep listening without requiring wake trigger.]] - `uses` [INFERRED]
- [[Play a system beep sound (Windows only).]] - `uses` [INFERRED]
- [[Start the audio manager.]] - `uses` [INFERRED]
- [[Test audio manager standalone (echo mode).]] - `uses` [INFERRED]
- [[_test()_3]] - `calls` [EXTRACTED]
- [[wake_detector.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/Community_29
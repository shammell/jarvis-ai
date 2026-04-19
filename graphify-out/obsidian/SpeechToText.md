---
source_file: "voice\speech_to_text.py"
type: "code"
community: "Community 29"
location: "L79"
tags:
  - graphify/code
  - graphify/INFERRED
  - community/Community_29
---

# SpeechToText

## Connections
- [[.__init__()_202]] - `calls` [INFERRED]
- [[.__init__()_204]] - `method` [EXTRACTED]
- [[._audio_to_wav()]] - `method` [EXTRACTED]
- [[._record_until_silence()]] - `method` [EXTRACTED]
- [[._transcribe_google()]] - `method` [EXTRACTED]
- [[._transcribe_groq()]] - `method` [EXTRACTED]
- [[.listen_and_transcribe()]] - `method` [EXTRACTED]
- [[AudioManager]] - `uses` [INFERRED]
- [[AudioManagerConfig]] - `uses` [INFERRED]
- [[AudioState]] - `uses` [INFERRED]
- [[BeepType]] - `uses` [INFERRED]
- [[Called when wake trigger fires (clap or wake word).]] - `uses` [INFERRED]
- [[Central audio controller with state machine.      Flow         IDLE - (clapwa]] - `uses` [INFERRED]
- [[Different beep sounds for different events.]] - `uses` [INFERRED]
- [[Immutable audio manager configuration.]] - `uses` [INFERRED]
- [[In continuous mode, keep listening without requiring wake trigger.]] - `uses` [INFERRED]
- [[Play a system beep sound (Windows only).]] - `uses` [INFERRED]
- [[Records audio from microphone and transcribes to text.      Usage         stt =]] - `rationale_for` [EXTRACTED]
- [[Start the audio manager.]] - `uses` [INFERRED]
- [[Test audio manager standalone (echo mode).]] - `uses` [INFERRED]
- [[_test()_1]] - `calls` [EXTRACTED]
- [[speech_to_text.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/INFERRED #community/Community_29
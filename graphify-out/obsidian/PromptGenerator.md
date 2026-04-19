---
source_file: "voice\prompt_generator.py"
type: "code"
community: "Community 11"
location: "L243"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Community_11
---

# PromptGenerator

## Connections
- [[.__init__()_203]] - `method` [EXTRACTED]
- [[._handle_create_code()]] - `method` [EXTRACTED]
- [[._handle_document_read()]] - `method` [EXTRACTED]
- [[._handle_general_query()]] - `method` [EXTRACTED]
- [[._handle_image_analyze()]] - `method` [EXTRACTED]
- [[._handle_open_app()]] - `method` [EXTRACTED]
- [[._handle_screen_analyze()]] - `method` [EXTRACTED]
- [[._handle_system_control()]] - `method` [EXTRACTED]
- [[._handle_type_text()]] - `method` [EXTRACTED]
- [[._handle_web_search()]] - `method` [EXTRACTED]
- [[._process_single_step()]] - `method` [EXTRACTED]
- [[.initialize()]] - `calls` [INFERRED]
- [[.process()_4]] - `method` [EXTRACTED]
- [[Bridge between voice system and JARVIS orchestrator.      Takes transcribed text]] - `uses` [INFERRED]
- [[Check if text looks like a high-level goal.]] - `uses` [INFERRED]
- [[Execute a high-level goal.]] - `uses` [INFERRED]
- [[Generates smart prompts and executes actions based on voice commands.      Usage]] - `rationale_for` [EXTRACTED]
- [[Handle a voice command and return response text.]] - `uses` [INFERRED]
- [[Initialize bridge with orchestrator connection.]] - `uses` [INFERRED]
- [[Shutdown the voice bridge.]] - `uses` [INFERRED]
- [[TaskChainExecutor_1]] - `uses` [INFERRED]
- [[VoiceBridge]] - `uses` [INFERRED]
- [[Wrap Groq client into a simple async callable.]] - `uses` [INFERRED]
- [[Wrap JARVIS LLM manager into a simple async callable.]] - `uses` [INFERRED]
- [[prompt_generator.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Community_11
---
source_file: "voice\task_chain_executor.py"
type: "code"
community: "Community 11"
location: "L471"
tags:
  - graphify/code
  - graphify/EXTRACTED
  - community/Community_11
---

# TaskChainExecutor

## Connections
- [[.__init__()_203]] - `calls` [INFERRED]
- [[.__init__()_207]] - `method` [EXTRACTED]
- [[._detect_task_type()]] - `method` [EXTRACTED]
- [[._execute_chain()]] - `method` [EXTRACTED]
- [[._execute_with_recovery()]] - `method` [EXTRACTED]
- [[._extract_app_name()]] - `method` [EXTRACTED]
- [[._extract_object()]] - `method` [EXTRACTED]
- [[._handle_complex_command()]] - `method` [EXTRACTED]
- [[._handle_recall()]] - `method` [EXTRACTED]
- [[._handle_resume()]] - `method` [EXTRACTED]
- [[._is_complex_command()]] - `method` [EXTRACTED]
- [[._is_resume_request()]] - `method` [EXTRACTED]
- [[._llm_parse()]] - `method` [EXTRACTED]
- [[._resolve_reference()]] - `method` [EXTRACTED]
- [[._rule_based_parse()]] - `method` [EXTRACTED]
- [[._should_continue_on_failure()]] - `method` [EXTRACTED]
- [[._update_context()]] - `method` [EXTRACTED]
- [[._update_context_from_task()]] - `method` [EXTRACTED]
- [[.clear_context()]] - `method` [EXTRACTED]
- [[.get_status()_3]] - `method` [EXTRACTED]
- [[.parse_complex_command()]] - `method` [EXTRACTED]
- [[.process()_5]] - `method` [EXTRACTED]
- [[Analyze current screen content.]] - `uses` [INFERRED]
- [[Analyze provided image path.]] - `uses` [INFERRED]
- [[Detect user's intent from transcribed text.]] - `uses` [INFERRED]
- [[Generate a filename from the command text.]] - `uses` [INFERRED]
- [[Generate code and open in VS Code.]] - `uses` [INFERRED]
- [[Generates smart prompts and executes actions based on voice commands.      Usage]] - `uses` [INFERRED]
- [[Handle general queries via LLM.]] - `uses` [INFERRED]
- [[Handle system control commands.]] - `uses` [INFERRED]
- [[Handle type text commands.          Examples             - Hello World likho]] - `uses` [INFERRED]
- [[IntentType]] - `uses` [INFERRED]
- [[Main executor for multi-step voice commands.      Features     - Parse complex]] - `rationale_for` [EXTRACTED]
- [[Open browser and search.]] - `uses` [INFERRED]
- [[Process a voice command and return response text.]] - `uses` [INFERRED]
- [[PromptGenerator]] - `uses` [INFERRED]
- [[Read and summarize PDFWordText documents.]] - `uses` [INFERRED]
- [[Remove markdown code fences from LLM output.]] - `uses` [INFERRED]
- [[task_chain_executor.py]] - `contains` [EXTRACTED]

#graphify/code #graphify/EXTRACTED #community/Community_11
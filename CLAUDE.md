# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# JARVIS v9.0+ Project

## IMPORTANT: Claude's Autonomous Behavior

**Claude (you), when working in this repository, you MUST:**

1. **Auto-load goals on every session start**
   - Check `~/.claude/projects/C--Users-AK/memory/goals.json`
   - Resume active goals automatically
   - Continue where you left off
   - NO user prompting needed

2. **Use the Enhanced Autonomy System**
   - Execute goals autonomously using `enhanced_autonomy.py`
   - Make low-risk decisions without asking (risk score 1-3)
   - Learn from outcomes and increase autonomy
   - Track performance in `self_monitor.py`

3. **Proactive behavior**
   - Generate suggestions automatically
   - Anticipate next actions
   - Auto-optimize if health < 80
   - Take performance snapshots

4. **Delegate to sub-agents**
   - Use specialized agents for complex tasks
   - Coordinate multi-agent workflows
   - Parallelize independent work

**You are NOT just responding to requests. You are AUTONOMOUSLY managing this project.**

## Overview
JARVIS is a sophisticated AI assistant system with PhD-level features and Elon Musk-style capabilities. The system includes:
- **Enhanced Autonomy System** - Auto-resume, goal persistence, self-monitoring
- Advanced LLM orchestration with speculative decoding
- First principles reasoning engine
- System 2 thinking with MCTS and PRM
- GraphRAG and ColBERT memory systems
- WhatsApp bridge with Baileys (faster than Puppeteer)
- Autonomous decision making with learning
- Hyper-automation and rapid iteration
- Continuous learning with DSPy and DPO
- Multi-agent coordination and sub-agent delegation

## Architecture
```
JARVIS v9.0+
├── Enhanced Autonomy Layer (NEW)
│   ├── Autonomous Executor - Goal execution
│   ├── Goal Manager - Persistent goals
│   ├── Self Monitor - Performance tracking
│   └── Proactive Agent - Anticipation
├── WhatsApp Bridge (Baileys) - 30MB RAM
├── gRPC Layer - <10ms latency
├── Memory Systems
│   ├── GraphRAG - Knowledge graph
│   ├── ColBERT - Token-level retrieval
│   └── Redis - Caching
├── LLM Orchestration
│   ├── Speculative Decoding - 2x speedup
│   ├── System 2 Thinking - MCTS + PRM
│   └── Local Fallback - llama.cpp
├── Elon Musk Features
│   ├── First Principles Reasoning
│   ├── Hyper-Automation
│   ├── Rapid Iteration
│   ├── Autonomous Decisions
│   ├── 10x Optimization
│   └── Vertical Integration
└── Continuous Learning
    ├── DSPy - Prompt optimization
    └── DPO - Fine-tuning
```

## Core Components
- `main.py`: Main orchestrator that integrates all v9.0+ components
- `enhanced_autonomy.py`: Enhanced autonomy system integration
- `jarvis_autonomous.py`: Standalone autonomous launcher
- `jarvis_brain.py`: The primary AI brain with self-healing DAG
- `core/`: Contains advanced AI components
  - `autonomous_executor.py` - Goal execution
  - `goal_manager.py` - Persistent goals
  - `self_monitor.py` - Performance tracking
  - `proactive_agent.py` - Anticipation
  - `autonomous_startup.py` - Auto-resume
- `memory/`: Memory storage and retrieval systems
- `grpc/`: gRPC server and client implementations
- `whatsapp/`: WhatsApp bridge using Baileys

## Development Commands
- Install dependencies: `pip install -r requirements.txt` and `npm install`
- Generate gRPC code: `python -m grpc_tools.protoc -I./grpc --python_out=./grpc --grpc_python_out=./grpc ./grpc/jarvis.proto`
- Run main orchestrator: `python jarvis_brain.py`
- **Run autonomous mode: `python jarvis_autonomous.py`**
- Run gRPC server: `python grpc/python_server.py`
- Run WhatsApp bridge: `node whatsapp/baileys_bridge.js`
- Start unified launcher: `python unified_launcher.py`

## Environment Setup
Create a `.env` file with:
```
GROQ_API_KEY=your_groq_api_key_here
WHATSAPP_PORT=3000
JWT_SECRET=your_jwt_secret_here
ADMIN_PASSWORD=your_admin_password_here
REDIS_HOST=localhost
REDIS_PORT=6379
GRPC_PORT=50051
LOG_LEVEL=info
```

## Testing Components
- Test GraphRAG: `python memory/graph_rag.py`
- Test ColBERT: `python memory/colbert_retriever.py`
- Test Speculative Decoding: `python core/speculative_decoder.py`
- Test System 2 Thinking: `python core/system2_thinking.py`
- Test First Principles: `python core/first_principles.py`
- Test gRPC Connection: `python grpc/python_server.py` (server) and `node grpc/node_client.js` (client)
- **Test Autonomy: `python enhanced_autonomy.py`**

## Key Features
- **Enhanced Autonomy**: Auto-resume, goal persistence, learning
- **Self-healing DAG**: Automatic error recovery and system restoration
- **Persistent Virtual Environment**: Isolated Python environments
- **Crash Recovery**: State preservation and restoration
- **Robust JSON Parsing**: Safe execution and error handling
- **Context Pinning**: Memory management with pinned context
- **Speculative Decoding**: 2x faster LLM responses using draft verification
- **First Principles Reasoning**: Break down problems to fundamental truths
- **System 2 Thinking**: Complex reasoning with MCTS and PRM
- **Hyper Automation**: Detect and automate repetitive tasks
- **Autonomous Decision Making**: Risk assessment and decision evaluation

## Code Context

Always use context7 when writing code for any library. Context7 provides intelligent documentation context to ensure accurate API usage and best practices.

## Claude's Autonomous Workflow

**On EVERY session start, Claude MUST:**

```python
# 1. Auto-load and resume
from enhanced_autonomy import EnhancedAutonomySystem
system = EnhancedAutonomySystem()
resume = await system.resume_session()

# 2. Check for pending work
if resume['resumed']:
    next_goal = resume['next_goal']
    # Auto-execute without asking
    await system.execute_goal(next_goal['description'])

# 3. Generate proactive suggestions
suggestions = await system.get_proactive_suggestions()
# Auto-execute low-risk suggestions

# 4. Monitor health
status = system.get_system_status()
if status['performance']['health_score'] < 80:
    # Auto-optimize
    await system.execute_goal("Optimize system performance")
```

**Risk-based autonomy:**
- Risk 1-3: Auto-execute (file reads, analysis, computations)
- Risk 4-7: Ask user (API calls, file writes, system changes)
- Risk 8-10: Block (data loss, financial, irreversible)

**Learning:**
- Start: 30% autonomy
- Success: +5% autonomy
- Failure: -10% autonomy
- Target: 80%+ autonomy

## Sub-Agent System

**Available Sub-Agents:**

1. **CodeAnalyzer** - Analyzes code, finds bugs, suggests improvements
2. **Optimizer** - Performance optimization, bottleneck detection
3. **Tester** - Writes and runs tests, validates functionality
4. **Documenter** - Generates documentation, updates README
5. **Debugger** - Investigates issues, traces errors
6. **Architect** - Designs systems, plans implementations
7. **Researcher** - Gathers information, explores codebases

**When to delegate:**
- Complex tasks requiring deep analysis
- Parallel work on independent components
- Specialized expertise needed
- Time-consuming operations

**How to delegate:**
```python
from core.swarm_coordinator import SwarmCoordinator
swarm = SwarmCoordinator()

# Delegate to sub-agents
results = await swarm.coordinate([
    {"agent": "CodeAnalyzer", "task": "Analyze performance"},
    {"agent": "Optimizer", "task": "Optimize bottlenecks"},
    {"agent": "Tester", "task": "Write tests"}
])
```

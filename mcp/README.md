# 🤖 JARVIS Terminal MCP Server
## Dusre Terminal ka Access + Auto Error Fixing

---

## Yeh Kya Karta Hai?

Jab aap Claude Code mein koi file ka zikar karte hain, Claude:
1. **Automatically dusre terminal mein file run karta hai**
2. **Errors detect karta hai** (port conflict, missing module, syntax error, etc.)
3. **Khud fix karta hai** - missing packages install karta hai, port free karta hai
4. **Dobara run karta hai** jab tak success na ho (max 3 tries)

---

## Windows Setup - Step by Step

### Step 1: Yeh folder apne PC pe copy karo
```
C:\Users\AK\jarvis-terminal-mcp\
├── server.js
├── package.json
└── setup_windows.bat
```

### Step 2: setup_windows.bat run karo
Double-click karein ya:
```cmd
cd C:\Users\AK\jarvis-terminal-mcp
setup_windows.bat
```

### Step 3: MCP Claude Code mein add karo
```cmd
claude mcp add jarvis-terminal --scope user -- node "C:\Users\AK\jarvis-terminal-mcp\server.js"
```

### Step 4: Verify karo
```cmd
claude mcp list
```
Output mein `jarvis-terminal` dikhna chahiye.

### Step 5: Claude Code restart karo
Claude Code band karo aur dobara kholo.

---

## Use Kaise Karo - Examples

### Example 1: Simple file run karo
Claude Code mein type karo:
```
main.py run karo mere jarvis_project folder mein
```

Claude automatically:
- `python C:\Users\AK\jarvis_project\main.py` run karega
- Errors dikhayega
- Fixes suggest karega

### Example 2: Auto-fix mode
```
auto_fix_and_run karo C:\Users\AK\jarvis_project\main_genesis.py
```

Claude:
- File run karega
- Agar `ModuleNotFoundError` aaya → `pip install` karega
- Agar port in use aaya → port free karega
- 3 baar try karega

### Example 3: Koi bhi command
```
ye command run karo dusre terminal mein: pip install fastapi uvicorn
```

---

## Available Tools

| Tool | Kya Karta Hai |
|------|--------------|
| `run_file` | Kisi bhi file ko run karo |
| `run_command` | Koi bhi terminal command run karo |
| `auto_fix_and_run` | Run + auto detect + auto fix + retry |
| `kill_process` | Running process band karo |
| `read_file` | File content parho |
| `write_file` | File mein likho (fix ke baad) |
| `get_system_info` | System info dekho |

---

## Auto-Fix Kya Kya Fix Kar Sakta Hai?

| Error | Auto Fix |
|-------|----------|
| `ModuleNotFoundError` | `pip install <module>` |
| `Cannot find module` | `npm install <module>` |
| Port already in use | Port pe process kill karta hai |
| `SyntaxError` | Claude ko batata hai code fix karne |
| `IndentationError` | Claude ko batata hai |
| `FileNotFoundError` | Path suggest karta hai |

---

## Troubleshooting

**MCP list mein nahi dikh raha?**
```cmd
claude mcp remove jarvis-terminal
claude mcp add jarvis-terminal --scope user -- node "C:\Users\AK\jarvis-terminal-mcp\server.js"
```

**node_modules nahi hai?**
```cmd
cd C:\Users\AK\jarvis-terminal-mcp
npm install
```

**node-pty install fail ho gaya?**
```cmd
npm install --global --production windows-build-tools
npm install
```

#!/usr/bin/env node
/**
 * JARVIS Terminal MCP Server - Enhanced with Holistic System Validation
 *
 * Yeh MCP server Claude Code ko dusre terminal ka access deta hai.
 * - Koi bhi file run karo
 * - Errors automatically detect hote hain
 * - Claude khud fix karta hai aur dobara run karta hai
 * - Chrome, WhatsApp, terminal validation added
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { spawn } from "child_process";
import { existsSync, readFileSync, writeFileSync } from "fs";
import { join, dirname, extname, basename } from "path";
import { platform, cpus, totalmem, freemem } from "os";
import stripAnsi from "strip-ansi";

const IS_WINDOWS = platform() === "win32";

// =============================================
// TERMINAL SESSION MANAGER
// Persistent shell jo commands run karta hai
// =============================================
class TerminalSession {
  constructor() {
    this.sessions = new Map(); // Multiple sessions support
    this.outputBuffers = new Map();
    this.runningProcesses = new Map();
  }

  // Ek command run karo aur output + errors wapas lo
  async runCommand(command, cwd, sessionId = "default", timeout = 60000) {
    return new Promise((resolve) => {
      const shell = IS_WINDOWS ? "cmd.exe" : "/bin/bash";
      const shellArgs = IS_WINDOWS ? ["/c", command] : ["-c", command];

      const startTime = Date.now();
      let stdout = "";
      let stderr = "";
      let timedOut = false;

      const proc = spawn(shell, shellArgs, {
        cwd: cwd || process.cwd(),
        env: { ...process.env },
        timeout: timeout,
      });

      this.runningProcesses.set(sessionId, proc);

      proc.stdout.on("data", (data) => {
        stdout += data.toString();
      });

      proc.stderr.on("data", (data) => {
        stderr += data.toString();
      });

      const timer = setTimeout(() => {
        timedOut = true;
        proc.kill();
        resolve({
          success: false,
          stdout: stripAnsi(stdout),
          stderr: "TIMEOUT: Command exceeded " + timeout / 1000 + " seconds",
          exitCode: -1,
          duration: Date.now() - startTime,
          timedOut: true,
        });
      }, timeout);

      proc.on("close", (code) => {
        if (!timedOut) {
          clearTimeout(timer);
          this.runningProcesses.delete(sessionId);
          resolve({
            success: code === 0,
            stdout: stripAnsi(stdout),
            stderr: stripAnsi(stderr),
            exitCode: code,
            duration: Date.now() - startTime,
            timedOut: false,
          });
        }
      });

      proc.on("error", (err) => {
        clearTimeout(timer);
        resolve({
          success: false,
          stdout: "",
          stderr: err.message,
          exitCode: -1,
          duration: Date.now() - startTime,
          timedOut: false,
        });
      });
    });
  }

  // Kisi running process ko band karo
  killSession(sessionId = "default") {
    const proc = this.runningProcesses.get(sessionId);
    if (proc) {
      proc.kill("SIGKILL");
      this.runningProcesses.delete(sessionId);
      return true;
    }
    return false;
  }
}

// =============================================
// ERROR ANALYZER
// Errors ko samjhta hai aur fix suggest karta hai
// =============================================
class ErrorAnalyzer {
  analyze(stderr, stdout, exitCode, filePath) {
    const allOutput = stderr + "\n" + stdout;
    const errors = [];

    // Python errors
    if (stderr.includes("ModuleNotFoundError") || stderr.includes("ImportError")) {
      const match = stderr.match(/No module named '([^']+)'/);
      if (match) {
        errors.push({
          type: "MISSING_MODULE",
          module: match[1],
          fix: `pip install ${match[1]}`,
          description: `Module '${match[1]}' install nahi hai`,
        });
      }
    }

    if (stderr.includes("SyntaxError")) {
      const lineMatch = stderr.match(/line (\d+)/);
      errors.push({
        type: "SYNTAX_ERROR",
        line: lineMatch ? lineMatch[1] : "unknown",
        description: "Python syntax galat hai - code check karo",
        fix: "code_fix_needed",
      });
    }

    if (stderr.includes("IndentationError")) {
      errors.push({
        type: "INDENTATION_ERROR",
        description: "Indentation galat hai",
        fix: "code_fix_needed",
      });
    }

    if (stderr.includes("PermissionError") || stderr.includes("EACCES")) {
      errors.push({
        type: "PERMISSION_ERROR",
        description: "Permission nahi hai is file/folder ka",
        fix: IS_WINDOWS
          ? "Run as Administrator"
          : `chmod +x ${filePath}`,
      });
    }

    // Port already in use (jaise aapka pehla wala error)
    if (stderr.includes("10048") || stderr.includes("EADDRINUSE") || stderr.includes("address already in use")) {
      const portMatch = stderr.match(/port[:\s]+(\d+)|:(\d+)\)/i) || allOutput.match(/(\d{4,5})/);
      const port = portMatch ? (portMatch[1] || portMatch[2]) : "8000";
      errors.push({
        type: "PORT_IN_USE",
        port: port,
        description: `Port ${port} pehle se use ho raha hai`,
        fix: IS_WINDOWS
          ? `netstat -ano | findstr :${port} then taskkill /PID <pid> /F`
          : `lsof -ti:${port} | xargs kill -9`,
        autoFix: IS_WINDOWS
          ? `for /f "tokens=5" %a in ('netstat -aon ^| findstr :${port}') do taskkill /f /pid %a`
          : `fuser -k ${port}/tcp`,
      });
    }

    // Node.js errors
    if (stderr.includes("Cannot find module")) {
      const match = stderr.match(/Cannot find module '([^']+)'/);
      if (match) {
        errors.push({
          type: "NODE_MODULE_MISSING",
          module: match[1],
          fix: `npm install ${match[1]}`,
          description: `Node module '${match[1]}' nahi mila`,
        });
      }
    }

    if (stderr.includes("npm ERR!")) {
      errors.push({
        type: "NPM_ERROR",
        description: "npm mein kuch gadbad hai",
        fix: "npm install",
      });
    }

    // File not found
    if (stderr.includes("FileNotFoundError") || stderr.includes("ENOENT") || stderr.includes("No such file")) {
      const match = stderr.match(/'([^']+)'|"([^"]+)"/);
      errors.push({
        type: "FILE_NOT_FOUND",
        file: match ? (match[1] || match[2]) : "unknown",
        description: "File ya folder nahi mila",
        fix: "path check karo",
      });
    }

    // Memory errors
    if (stderr.includes("MemoryError") || stderr.includes("ENOMEM")) {
      errors.push({
        type: "MEMORY_ERROR",
        description: "RAM kam pad gayi",
        fix: "memory optimize karo ya RAM free karo",
      });
    }

    return errors;
  }

  // Kaunsa command use karna chahiye file run karne ke liye
  getRunCommand(filePath) {
    const ext = extname(filePath).toLowerCase();
    const fileName = basename(filePath);

    const commands = {
      ".py": `python "${filePath}"`,
      ".js": `node "${filePath}"`,
      ".ts": `npx ts-node "${filePath}"`,
      ".sh": IS_WINDOWS ? `bash "${filePath}"` : `bash "${filePath}"`,
      ".bat": `"${filePath}"`,
      ".ps1": `powershell -File "${filePath}"`,
      ".go": `go run "${filePath}"`,
      ".rb": `ruby "${filePath}"`,
      ".php": `php "${filePath}"`,
      ".java": `cd "${dirname(filePath)}" && javac "${fileName}" && java "${basename(fileName, '.java')}"`,
      ".cpp": IS_WINDOWS
        ? `cd "${dirname(filePath)}" && g++ "${fileName}" -o output.exe && output.exe`
        : `cd "${dirname(filePath)}" && g++ "${fileName}" -o output && ./output`,
      ".rs": `cd "${dirname(filePath)}" && cargo run`,
    };

    return commands[ext] || `"${filePath}"`;
  }
}

// =============================================
// SYSTEM VALIDATOR
// Validates Chrome, WhatsApp, and Terminal
// =============================================
class SystemValidator {
  constructor() {
    this.terminal = new TerminalSession();
  }

  // Validate Chrome installation and accessibility
  async validateChrome() {
    try {
      let result;

      if (IS_WINDOWS) {
        // Try different ways to check Chrome on Windows
        result = await this.terminal.runCommand('where chrome', null, 'chrome_check', 5000);
        if (result.exitCode !== 0) {
          result = await this.terminal.runCommand('where googlechrome', null, 'chrome_check', 5000);
        }
        if (result.exitCode !== 0) {
          // Check registry for Chrome
          result = await this.terminal.runCommand('reg query "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\App Paths\\chrome.exe"', null, 'chrome_check', 5000);
        }
      } else {
        // On macOS/Linux
        result = await this.terminal.runCommand('which google-chrome', null, 'chrome_check', 5000);
        if (result.exitCode !== 0) {
          result = await this.terminal.runCommand('which chromium-browser', null, 'chrome_check', 5000);
        }
      }

      const chromeInstalled = result.success;

      // Try to get Chrome version
      let versionResult;
      if (IS_WINDOWS) {
        versionResult = await this.terminal.runCommand('wmic datafile where name="C:\\\\Program Files\\\\Google\\\\Chrome\\\\Application\\\\chrome.exe" get Version', null, 'chrome_version', 5000);
      } else {
        versionResult = await this.terminal.runCommand('google-chrome --version || chromium-browser --version', null, 'chrome_version', 5000);
      }

      return {
        installed: chromeInstalled,
        version: versionResult.success ? versionResult.stdout.trim() : "Unknown",
        accessible: result.success,
        status: chromeInstalled ? "OK" : "Not Found"
      };
    } catch (error) {
      return {
        installed: false,
        version: "Unknown",
        accessible: false,
        status: "Error checking Chrome",
        error: error.message
      };
    }
  }

  // Validate WhatsApp bridge (check if service is running)
  async validateWhatsApp() {
    try {
      // Check if WhatsApp bridge is running on port 3000
      let portCheck;
      if (IS_WINDOWS) {
        portCheck = await this.terminal.runCommand('netstat -an | findstr :3000', null, 'whatsapp_port_check', 5000);
      } else {
        portCheck = await this.terminal.runCommand('netstat -tlnp | grep :3000 || lsof -i :3000', null, 'whatsapp_port_check', 5000);
      }

      // Check if WhatsApp directory exists and has the necessary files
      const whatsappDirExists = existsSync('./whatsapp');
      const baileysBridgeExists = existsSync('./whatsapp/baileys_bridge.js');

      // Check if npm modules are installed in whatsapp directory
      let npmCheck = { success: false };
      if (whatsappDirExists) {
        npmCheck = await this.terminal.runCommand('npm list @whiskeysockets/baileys', './whatsapp', 'whatsapp_npm_check', 5000);
      }

      return {
        serviceRunning: portCheck.success && (portCheck.stdout.includes('LISTEN') || portCheck.stdout.includes('ESTABLISHED')),
        directoryExists: whatsappDirExists,
        bridgeExists: baileysBridgeExists,
        modulesInstalled: npmCheck.success,
        status: portCheck.success && whatsappDirExists && baileysBridgeExists ? "OK" : "Issues found"
      };
    } catch (error) {
      return {
        serviceRunning: false,
        directoryExists: false,
        bridgeExists: false,
        modulesInstalled: false,
        status: "Error validating WhatsApp",
        error: error.message
      };
    }
  }

  // Validate terminal and system capabilities
  async validateTerminal() {
    try {
      // Check if basic commands work
      const pythonCheck = await this.terminal.runCommand('python --version', null, 'py_check', 5000);
      const nodeCheck = await this.terminal.runCommand('node --version', null, 'node_check', 5000);
      const npmCheck = await this.terminal.runCommand('npm --version', null, 'npm_check', 5000);

      // System info
      const cpuInfo = cpus();
      const totalRam = totalmem();
      const freeRam = freemem();

      return {
        pythonAvailable: pythonCheck.success,
        nodeAvailable: nodeCheck.success,
        npmAvailable: npmCheck.success,
        pythonVersion: pythonCheck.stdout ? pythonCheck.stdout.trim() : "Not found",
        nodeVersion: nodeCheck.stdout ? nodeCheck.stdout.trim() : "Not found",
        npmVersion: npmCheck.stdout ? npmCheck.stdout.trim() : "Not found",
        cpuCount: cpuInfo.length,
        cpuModel: cpuInfo[0]?.model,
        totalRam: Math.round(totalRam / (1024 * 1024 * 1024)) + " GB",
        freeRam: Math.round(freeRam / (1024 * 1024 * 1024)) + " GB",
        osPlatform: platform(),
        status: pythonCheck.success && nodeCheck.success ? "OK" : "Missing essentials"
      };
    } catch (error) {
      return {
        pythonAvailable: false,
        nodeAvailable: false,
        npmAvailable: false,
        status: "Error validating terminal",
        error: error.message
      };
    }
  }

  // Perform complete holistic validation
  async validateCompleteSystem() {
    const chromeValidation = await this.validateChrome();
    const whatsappValidation = await this.validateWhatsApp();
    const terminalValidation = await this.validateTerminal();

    // Overall health assessment
    const healthScore = (
      (chromeValidation.installed ? 1 : 0) +
      (whatsappValidation.directoryExists ? 1 : 0) +
      (whatsappValidation.bridgeExists ? 1 : 0) +
      (whatsappValidation.serviceRunning ? 1 : 0) +
      (terminalValidation.pythonAvailable ? 1 : 0) +
      (terminalValidation.nodeAvailable ? 1 : 0)
    ) / 6;

    const overallStatus = healthScore >= 0.8 ? "EXCELLENT" :
                         healthScore >= 0.6 ? "GOOD" :
                         healthScore >= 0.4 ? "FAIR" : "POOR";

    return {
      timestamp: new Date().toISOString(),
      overallHealth: overallStatus,
      healthScore: Math.round(healthScore * 100),
      chrome: chromeValidation,
      whatsapp: whatsappValidation,
      terminal: terminalValidation,
      recommendations: this.generateRecommendations(chromeValidation, whatsappValidation, terminalValidation)
    };
  }

  // Generate recommendations based on validations
  generateRecommendations(chrome, whatsapp, terminal) {
    const recommendations = [];

    // Chrome recommendations
    if (!chrome.installed) {
      recommendations.push("Install Google Chrome for full browser automation capabilities");
    }

    // WhatsApp recommendations
    if (!whatsapp.directoryExists) {
      recommendations.push("WhatsApp bridge directory not found - ensure the project has the WhatsApp integration components");
    } else if (!whatsapp.bridgeExists) {
      recommendations.push("WhatsApp bridge file (baileys_bridge.js) not found - this is needed for WhatsApp functionality");
    } else if (!whatsapp.serviceRunning) {
      recommendations.push("WhatsApp bridge service is not running - start it with: node whatsapp/baileys_bridge.js");
    }

    // Terminal recommendations
    if (!terminal.pythonAvailable) {
      recommendations.push("Python not found - install Python 3.10+ for JARVIS core functionality");
    }
    if (!terminal.nodeAvailable) {
      recommendations.push("Node.js not found - install Node.js 18+ for JARVIS web and WhatsApp components");
    }
    if (!terminal.npmAvailable) {
      recommendations.push("npm not found - this is needed for managing JavaScript dependencies");
    }

    if (recommendations.length === 0) {
      recommendations.push("System is properly configured for JARVIS operation");
    }

    return recommendations;
  }
}

// =============================================
// MCP SERVER SETUP
// =============================================
const terminal = new TerminalSession();
const analyzer = new ErrorAnalyzer();
const validator = new SystemValidator();

const server = new Server(
  {
    name: "jarvis-terminal-mcp-enhanced",
    version: "2.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// =============================================
// TOOLS LIST
// =============================================
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "run_file",
        description:
          "Kisi bhi file ko dusre terminal mein run karo. Automatically detect karta hai Python, Node.js, etc. Errors analyze karta hai aur fix suggestions deta hai.",
        inputSchema: {
          type: "object",
          properties: {
            file_path: {
              type: "string",
              description: "Full path of the file to run (e.g., C:\\Users\\AK\\jarvis_project\\main.py)",
            },
            args: {
              type: "string",
              description: "Extra arguments (optional)",
            },
            timeout: {
              type: "number",
              description: "Timeout in seconds (default: 60)",
            },
            session_id: {
              type: "string",
              description: "Terminal session ID (default: 'main')",
            },
          },
          required: ["file_path"],
        },
      },
      {
        name: "run_command",
        description:
          "Koi bhi terminal command run karo dusre terminal mein. cd, pip install, npm install, etc.",
        inputSchema: {
          type: "object",
          properties: {
            command: {
              type: "string",
              description: "Command to run (e.g., 'pip install fastapi', 'npm install')",
            },
            cwd: {
              type: "string",
              description: "Working directory (optional)",
            },
            timeout: {
              type: "number",
              description: "Timeout in seconds (default: 120)",
            },
            session_id: {
              type: "string",
              description: "Terminal session ID",
            },
          },
          required: ["command"],
        },
      },
      {
        name: "auto_fix_and_run",
        description:
          "File run karo, agar error aaye toh automatically fix karo aur dobara run karo. Claude khud errors analyze karta hai.",
        inputSchema: {
          type: "object",
          properties: {
            file_path: {
              type: "string",
              description: "File path to run and auto-fix",
            },
            max_retries: {
              type: "number",
              description: "Kitni baar try kare (default: 3)",
            },
            auto_install: {
              type: "boolean",
              description: "Missing packages automatically install kare? (default: true)",
            },
          },
          required: ["file_path"],
        },
      },
      {
        name: "kill_process",
        description: "Kisi running process ya session ko band karo",
        inputSchema: {
          type: "object",
          properties: {
            session_id: {
              type: "string",
              description: "Session ID to kill (default: 'main')",
            },
          },
        },
      },
      {
        name: "read_file",
        description: "Kisi file ka content parho (errors fix karne ke liye)",
        inputSchema: {
          type: "object",
          properties: {
            file_path: {
              type: "string",
              description: "File path to read",
            },
          },
          required: ["file_path"],
        },
      },
      {
        name: "write_file",
        description: "File mein content likho (errors fix karne ke baad)",
        inputSchema: {
          type: "object",
          properties: {
            file_path: {
              type: "string",
              description: "File path to write",
            },
            content: {
              type: "string",
              description: "New content to write",
            },
          },
          required: ["file_path", "content"],
        },
      },
      {
        name: "get_system_info",
        description: "System info dekho - OS, Python version, Node version, etc.",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "validate_chrome",
        description: "Validate Chrome installation and accessibility for browser automation",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "validate_whatsapp",
        description: "Validate WhatsApp bridge functionality and service status",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "validate_terminal",
        description: "Validate terminal and system capabilities (Python, Node.js, etc.)",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
      {
        name: "validate_complete_system",
        description: "Perform holistic system validation including Chrome, WhatsApp, and terminal",
        inputSchema: {
          type: "object",
          properties: {},
        },
      },
    ],
  };
});

// =============================================
// TOOL HANDLERS
// =============================================
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    // ---- TOOL: run_file ----
    if (name === "run_file") {
      const { file_path, args: fileArgs = "", timeout = 60, session_id = "main" } = args;

      if (!existsSync(file_path)) {
        return {
          content: [
            {
              type: "text",
              text: `❌ FILE NAHI MILI: ${file_path}\n\nPath check karo!`,
            },
          ],
        };
      }

      let command = analyzer.getRunCommand(file_path);
      if (fileArgs) command += ` ${fileArgs}`;

      const cwd = dirname(file_path);
      const result = await terminal.runCommand(command, cwd, session_id, timeout * 1000);
      const errors = analyzer.analyze(result.stderr, result.stdout, result.exitCode, file_path);

      let response = `🖥️ TERMINAL OUTPUT\n`;
      response += `📁 File: ${file_path}\n`;
      response += `⚡ Command: ${command}\n`;
      response += `⏱️ Duration: ${result.duration}ms\n`;
      response += `🔢 Exit Code: ${result.exitCode}\n\n`;

      if (result.stdout) {
        response += `✅ STDOUT:\n${result.stdout}\n\n`;
      }

      if (result.stderr) {
        response += `❌ STDERR:\n${result.stderr}\n\n`;
      }

      if (errors.length > 0) {
        response += `🔍 DETECTED ERRORS:\n`;
        errors.forEach((err, i) => {
          response += `\n${i + 1}. [${err.type}] ${err.description}\n`;
          response += `   💊 Fix: ${err.fix}\n`;
          if (err.autoFix) response += `   🤖 Auto-Fix Command: ${err.autoFix}\n`;
        });
      }

      if (result.success) {
        response += `\n✅ SUCCESSFULLY COMPLETED!`;
      } else {
        response += `\n❌ FAILED - Errors fix karke dobara try karo`;
      }

      return { content: [{ type: "text", text: response }] };
    }

    // ---- TOOL: run_command ----
    if (name === "run_command") {
      const { command, cwd, timeout = 120, session_id = "main" } = args;

      const result = await terminal.runCommand(command, cwd, session_id, timeout * 1000);
      const errors = analyzer.analyze(result.stderr, result.stdout, result.exitCode, "");

      let response = `🖥️ COMMAND RESULT\n`;
      response += `💻 Command: ${command}\n`;
      response += `📂 CWD: ${cwd || "default"}\n`;
      response += `⏱️ Duration: ${result.duration}ms\n`;
      response += `🔢 Exit Code: ${result.exitCode}\n\n`;

      if (result.stdout) response += `📤 OUTPUT:\n${result.stdout}\n\n`;
      if (result.stderr) response += `⚠️ ERRORS:\n${result.stderr}\n\n`;

      if (errors.length > 0) {
        response += `🔍 ANALYSIS:\n`;
        errors.forEach((err) => {
          response += `• [${err.type}] ${err.description} → Fix: ${err.fix}\n`;
        });
      }

      response += result.success ? "\n✅ SUCCESS" : "\n❌ FAILED";

      return { content: [{ type: "text", text: response }] };
    }

    // ---- TOOL: auto_fix_and_run ----
    if (name === "auto_fix_and_run") {
      const { file_path, max_retries = 3, auto_install = true } = args;

      if (!existsSync(file_path)) {
        return {
          content: [{ type: "text", text: `❌ File nahi mili: ${file_path}` }],
        };
      }

      let log = `🤖 AUTO-FIX MODE STARTED\n`;
      log += `📁 File: ${file_path}\n`;
      log += `🔄 Max Retries: ${max_retries}\n\n`;

      let attempt = 0;
      let lastResult = null;

      while (attempt < max_retries) {
        attempt++;
        log += `━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;
        log += `🔄 ATTEMPT ${attempt}/${max_retries}\n`;
        log += `━━━━━━━━━━━━━━━━━━━━━━━━━━━\n`;

        const command = analyzer.getRunCommand(file_path);
        const cwd = dirname(file_path);
        lastResult = await terminal.runCommand(command, cwd, `auto_${attempt}`, 60000);

        log += `Exit Code: ${lastResult.exitCode}\n`;
        if (lastResult.stdout) log += `Output: ${lastResult.stdout.substring(0, 500)}\n`;
        if (lastResult.stderr) log += `Error: ${lastResult.stderr.substring(0, 500)}\n`;

        if (lastResult.success) {
          log += `\n🎉 SUCCESS on attempt ${attempt}!\n`;
          break;
        }

        // Auto-fix: missing packages install karo
        const errors = analyzer.analyze(lastResult.stderr, lastResult.stdout, lastResult.exitCode, file_path);

        if (errors.length === 0) {
          log += `\n❓ Unknown error - manual check needed\n`;
          break;
        }

        let fixApplied = false;
        for (const err of errors) {
          log += `\n🔧 Fixing: [${err.type}] ${err.description}\n`;

          if (auto_install && err.type === "MISSING_MODULE") {
            log += `📦 Installing: pip install ${err.module}\n`;
            const installResult = await terminal.runCommand(
              `pip install ${err.module}`,
              cwd,
              "installer"
            );
            log += installResult.success
              ? `✅ Installed successfully!\n`
              : `❌ Install failed: ${installResult.stderr}\n`;
            fixApplied = installResult.success;
          }

          if (auto_install && err.type === "NODE_MODULE_MISSING") {
            const modName = err.module.startsWith(".") ? "" : err.module;
            if (modName) {
              log += `📦 Installing: npm install ${modName}\n`;
              const installResult = await terminal.runCommand(
                `npm install ${modName}`,
                cwd,
                "installer"
              );
              log += installResult.success ? `✅ Installed!\n` : `❌ Failed: ${installResult.stderr}\n`;
              fixApplied = installResult.success;
            }
          }

          if (err.type === "PORT_IN_USE" && err.autoFix) {
            log += `🔌 Killing port process: ${err.autoFix}\n`;
            const killResult = await terminal.runCommand(err.autoFix, cwd, "port_killer", 10000);
            log += killResult.success ? `✅ Port freed!\n` : `⚠️ Could not auto-kill, try manually\n`;
            fixApplied = true;
          }

          if (err.type === "SYNTAX_ERROR" || err.type === "INDENTATION_ERROR") {
            log += `📝 Code fix needed - Claude ko file ka content do taake wo fix kare\n`;
            log += `   Use 'read_file' tool to get content, fix it, then use 'write_file'\n`;
            fixApplied = false;
            break;
          }
        }

        if (!fixApplied && attempt < max_retries) {
          log += `⏳ Waiting before retry...\n`;
          await new Promise((r) => setTimeout(r, 1000));
        }
      }

      if (!lastResult?.success) {
        log += `\n❌ ALL ${max_retries} ATTEMPTS FAILED\n`;
        log += `💡 Manual intervention needed:\n`;
        const errors = analyzer.analyze(lastResult?.stderr || "", lastResult?.stdout || "", -1, file_path);
        errors.forEach((err) => {
          log += `   • ${err.description}: ${err.fix}\n`;
        });
      }

      return { content: [{ type: "text", text: log }] };
    }

    // ---- TOOL: kill_process ----
    if (name === "kill_process") {
      const { session_id = "main" } = args;
      const killed = terminal.killSession(session_id);
      return {
        content: [
          {
            type: "text",
            text: killed
              ? `✅ Session '${session_id}' band kar diya`
              : `⚠️ Session '${session_id}' already band tha`,
          },
        ],
      };
    }

    // ---- TOOL: read_file ----
    if (name === "read_file") {
      const { file_path } = args;
      if (!existsSync(file_path)) {
        return { content: [{ type: "text", text: `❌ File nahi mili: ${file_path}` }] };
      }
      const content = readFileSync(file_path, "utf-8");
      return {
        content: [
          {
            type: "text",
            text: `📄 FILE: ${file_path}\n\n${content}`,
          },
        ],
      };
    }

    // ---- TOOL: write_file ----
    if (name === "write_file") {
      const { file_path, content } = args;
      writeFileSync(file_path, content, "utf-8");
      return {
        content: [
          {
            type: "text",
            text: `✅ File save ho gayi: ${file_path}`,
          },
        ],
      };
    }

    // ---- TOOL: get_system_info ----
    if (name === "get_system_info") {
      const [pyVersion, nodeVersion, npmVersion] = await Promise.all([
        terminal.runCommand("python --version", null, "sysinfo1", 5000),
        terminal.runCommand("node --version", null, "sysinfo2", 5000),
        terminal.runCommand("npm --version", null, "sysinfo3", 5000),
      ]);

      const info = `💻 SYSTEM INFO\n
🖥️  OS: ${platform()}
🐍  Python: ${pyVersion.stdout.trim() || pyVersion.stderr.trim() || "Not found"}
🟢  Node.js: ${nodeVersion.stdout.trim() || "Not found"}
📦  npm: ${npmVersion.stdout.trim() || "Not found"}
📂  CWD: ${process.cwd()}`;

      return { content: [{ type: "text", text: info }] };
    }

    // ---- TOOL: validate_chrome ----
    if (name === "validate_chrome") {
      const validation = await validator.validateChrome();
      let response = `🔍 CHROME VALIDATION RESULTS\n\n`;
      response += `✅ Installed: ${validation.installed ? "Yes" : "No"}\n`;
      response += `🏷️  Version: ${validation.version}\n`;
      response += `📡 Accessible: ${validation.accessible ? "Yes" : "No"}\n`;
      response += `📊 Status: ${validation.status}\n`;

      if (validation.error) {
        response += `\n❌ Error: ${validation.error}`;
      }

      return { content: [{ type: "text", text: response }] };
    }

    // ---- TOOL: validate_whatsapp ----
    if (name === "validate_whatsapp") {
      const validation = await validator.validateWhatsApp();
      let response = `💬 WHATSAPP BRIDGE VALIDATION RESULTS\n\n`;
      response += `🔌 Service Running: ${validation.serviceRunning ? "Yes" : "No"}\n`;
      response += `📁 Directory Exists: ${validation.directoryExists ? "Yes" : "No"}\n`;
      response += `🤖 Bridge File Exists: ${validation.bridgeExists ? "Yes" : "No"}\n`;
      response += `📦 Modules Installed: ${validation.modulesInstalled ? "Yes" : "No"}\n`;
      response += `📊 Status: ${validation.status}\n`;

      if (validation.error) {
        response += `\n❌ Error: ${validation.error}`;
      }

      return { content: [{ type: "text", text: response }] };
    }

    // ---- TOOL: validate_terminal ----
    if (name === "validate_terminal") {
      const validation = await validator.validateTerminal();
      let response = `🖥️ TERMINAL VALIDATION RESULTS\n\n`;
      response += `🐍 Python Available: ${validation.pythonAvailable ? "Yes" : "No"}\n`;
      response += `   Version: ${validation.pythonVersion}\n\n`;
      response += `🟢 Node.js Available: ${validation.nodeAvailable ? "Yes" : "No"}\n`;
      response += `   Version: ${validation.nodeVersion}\n\n`;
      response += `📦 npm Available: ${validation.npmAvailable ? "Yes" : "No"}\n`;
      response += `   Version: ${validation.npmVersion}\n\n`;
      response += `🖥️  CPU Cores: ${validation.cpuCount}\n`;
      response += `💾 Total RAM: ${validation.totalRam}\n`;
      response += `📉 Free RAM: ${validation.freeRam}\n`;
      response += `🌐 OS Platform: ${validation.osPlatform}\n`;
      response += `📊 Status: ${validation.status}\n`;

      if (validation.error) {
        response += `\n❌ Error: ${validation.error}`;
      }

      return { content: [{ type: "text", text: response }] };
    }

    // ---- TOOL: validate_complete_system ----
    if (name === "validate_complete_system") {
      const validation = await validator.validateCompleteSystem();
      let response = `🎯 COMPLETE SYSTEM VALIDATION\n`;
      response += `🕐 Timestamp: ${validation.timestamp}\n`;
      response += `🌟 Overall Health: ${validation.overallHealth}\n`;
      response += `📈 Health Score: ${validation.healthScore}%\n\n`;

      response += `🔍 CHROME VALIDATION:\n`;
      response += `   ✅ Installed: ${validation.chrome.installed}\n`;
      response += `   🏷️  Version: ${validation.chrome.version}\n`;
      response += `   📊 Status: ${validation.chrome.status}\n\n`;

      response += `🔍 WHATSAPP VALIDATION:\n`;
      response += `   🔌 Service Running: ${validation.whatsapp.serviceRunning}\n`;
      response += `   📁 Directory Exists: ${validation.whatsapp.directoryExists}\n`;
      response += `   🤖 Bridge Exists: ${validation.whatsapp.bridgeExists}\n`;
      response += `   📦 Modules Installed: ${validation.whatsapp.modulesInstalled}\n`;
      response += `   📊 Status: ${validation.whatsapp.status}\n\n`;

      response += `🔍 TERMINAL VALIDATION:\n`;
      response += `   🐍 Python Available: ${validation.terminal.pythonAvailable}\n`;
      response += `   🟢 Node.js Available: ${validation.terminal.nodeAvailable}\n`;
      response += `   📦 npm Available: ${validation.terminal.npmAvailable}\n`;
      response += `   💾 Free RAM: ${validation.terminal.freeRam}\n`;
      response += `   📊 Status: ${validation.terminal.status}\n\n`;

      response += `💡 RECOMMENDATIONS:\n`;
      validation.recommendations.forEach((rec, i) => {
        response += `   ${i + 1}. ${rec}\n`;
      });

      return { content: [{ type: "text", text: response }] };
    }

    return {
      content: [{ type: "text", text: `❓ Unknown tool: ${name}` }],
    };
  } catch (error) {
    return {
      content: [
        {
          type: "text",
          text: `💥 MCP Server Error: ${error.message}\n${error.stack}`,
        },
      ],
    };
  }
});

// =============================================
// START SERVER
// =============================================
const transport = new StdioServerTransport();
await server.connect(transport);
console.error("🚀 JARVIS Terminal MCP Server (Enhanced) running...");
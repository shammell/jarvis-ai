#!/usr/bin/env node
/**
 * Computer Control MCP Server
 * Gives Claude full visual control over your computer
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { spawn } from "child_process";
import { platform } from "os";

const IS_WINDOWS = platform() === "win32";
const PYTHON_CMD = IS_WINDOWS ? "python" : "python3";

class ComputerControlServer {
  constructor() {
    this.server = new Server(
      {
        name: "computer-control",
        version: "1.0.0",
      },
      {
        capabilities: {
          tools: {},
        },
      }
    );

    this.setupHandlers();
  }

  setupHandlers() {
    this.server.setRequestHandler(ListToolsRequestSchema, async () => ({
      tools: [
        {
          name: "screenshot",
          description: "Capture screen and return base64 image",
          inputSchema: {
            type: "object",
            properties: {
              region: {
                type: "array",
                description: "Optional [x, y, width, height]",
                items: { type: "number" },
              },
            },
          },
        },
        {
          name: "mouse_move",
          description: "Move mouse to position",
          inputSchema: {
            type: "object",
            properties: {
              x: { type: "number" },
              y: { type: "number" },
              duration: { type: "number", default: 0.5 },
            },
            required: ["x", "y"],
          },
        },
        {
          name: "mouse_click",
          description: "Click mouse",
          inputSchema: {
            type: "object",
            properties: {
              x: { type: "number" },
              y: { type: "number" },
              button: { type: "string", enum: ["left", "right", "middle"], default: "left" },
              clicks: { type: "number", default: 1 },
            },
          },
        },
        {
          name: "keyboard_type",
          description: "Type text",
          inputSchema: {
            type: "object",
            properties: {
              text: { type: "string" },
              interval: { type: "number", default: 0.05 },
            },
            required: ["text"],
          },
        },
        {
          name: "keyboard_press",
          description: "Press key (enter, esc, tab, etc)",
          inputSchema: {
            type: "object",
            properties: {
              key: { type: "string" },
              presses: { type: "number", default: 1 },
            },
            required: ["key"],
          },
        },
        {
          name: "keyboard_hotkey",
          description: "Press hotkey combo (ctrl+c, etc)",
          inputSchema: {
            type: "object",
            properties: {
              keys: {
                type: "array",
                items: { type: "string" },
              },
            },
            required: ["keys"],
          },
        },
      ],
    }));

    this.server.setRequestHandler(CallToolRequestSchema, async (request) => {
      const { name, arguments: args } = request.params;

      try {
        const result = await this.executeCommand(name, args || {});
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify(result, null, 2),
            },
          ],
        };
      } catch (error) {
        return {
          content: [
            {
              type: "text",
              text: JSON.stringify({ success: false, error: error.message }),
            },
          ],
          isError: true,
        };
      }
    });
  }

  async executeCommand(command, args) {
    return new Promise((resolve, reject) => {
      const argsJson = JSON.stringify(args).replace(/\\/g, "\\\\").replace(/"/g, '\\"');

      const pythonScript = `
import sys
import json
sys.path.insert(0, 'C:/Users/AK/jarvis_project')
from computer_control_agent import ComputerControlAgent

agent = ComputerControlAgent()
args = json.loads('${argsJson}')
result = agent.execute('${command}', **args)
print(json.dumps(result))
`;

      const proc = spawn(PYTHON_CMD, ["-c", pythonScript], {
        cwd: "C:/Users/AK/jarvis_project",
      });

      let stdout = "";
      let stderr = "";

      proc.stdout.on("data", (data) => {
        stdout += data.toString();
      });

      proc.stderr.on("data", (data) => {
        stderr += data.toString();
      });

      proc.on("close", (code) => {
        if (code === 0) {
          try {
            const result = JSON.parse(stdout.trim());
            resolve(result);
          } catch (e) {
            resolve({ success: true, output: stdout });
          }
        } else {
          reject(new Error(stderr || `Process exited with code ${code}`));
        }
      });
    });
  }

  async run() {
    const transport = new StdioServerTransport();
    await this.server.connect(transport);
    console.error("Computer Control MCP Server running...");
  }
}

const server = new ComputerControlServer();
server.run().catch(console.error);

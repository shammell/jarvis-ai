#!/usr/bin/env node
/**
 * INTELLIGENT CONTROL MCP SERVER
 * Real PhD-level automation with learning capabilities
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

class IntelligentControlMCP {
  constructor() {
    this.server = new Server(
      {
        name: "intelligent-control",
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
          name: "find_chrome",
          description: "Find Chrome windows with detailed information",
          inputSchema: {
            type: "object",
            properties: {
              profile: { type: "string", description: "Profile name (optional)" },
            },
          },
        },
        {
          name: "smart_open_tab",
          description: "Open new tab with verification and retry",
          inputSchema: {
            type: "object",
            properties: {
              profile: { type: "string", description: "Profile name (optional)" },
            },
          },
        },
        {
          name: "smart_navigate",
          description: "Navigate to URL with intelligent retry",
          inputSchema: {
            type: "object",
            properties: {
              url: { type: "string", description: "URL to navigate to" },
              profile: { type: "string", description: "Profile name (optional)" },
            },
            required: ["url"],
          },
        },
        {
          name: "execute_workflow",
          description: "Execute multi-step workflow with learning",
          inputSchema: {
            type: "object",
            properties: {
              workflow: {
                type: "array",
                description: "Array of workflow steps",
                items: {
                  type: "object",
                  properties: {
                    action: { type: "string" },
                    url: { type: "string" },
                    seconds: { type: "number" },
                  },
                },
              },
              profile: { type: "string", description: "Profile name (optional)" },
            },
            required: ["workflow"],
          },
        },
        {
          name: "get_performance_insights",
          description: "Get learned performance statistics",
          inputSchema: {
            type: "object",
            properties: {},
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

from intelligent_automation import IntelligentAutomation

automation = IntelligentAutomation()
args = json.loads('${argsJson}')

if '${command}' == 'find_chrome':
    chrome = automation.find_chrome_by_profile(args.get('profile'))
    if chrome:
        result = {
            'success': True,
            'chrome': {
                'title': chrome['title'],
                'pid': chrome['pid'],
                'hwnd': chrome['hwnd']
            }
        }
    else:
        result = {'success': False, 'error': 'No Chrome found'}

elif '${command}' == 'smart_open_tab':
    chrome = automation.find_chrome_by_profile(args.get('profile'))
    if chrome:
        action_result = automation.smart_open_tab(chrome)
        result = {
            'success': action_result.success,
            'duration': action_result.duration,
            'screen_change': action_result.screen_change_percent,
            'metadata': action_result.metadata
        }
    else:
        result = {'success': False, 'error': 'No Chrome found'}

elif '${command}' == 'smart_navigate':
    chrome = automation.find_chrome_by_profile(args.get('profile'))
    if chrome:
        action_result = automation.smart_navigate(chrome, args['url'])
        result = {
            'success': action_result.success,
            'duration': action_result.duration,
            'screen_change': action_result.screen_change_percent,
            'url': args['url'],
            'metadata': action_result.metadata
        }
    else:
        result = {'success': False, 'error': 'No Chrome found'}

elif '${command}' == 'execute_workflow':
    chrome = automation.find_chrome_by_profile(args.get('profile'))
    if chrome:
        result = automation.execute_intelligent_workflow(chrome, args['workflow'])
        result['success'] = True
    else:
        result = {'success': False, 'error': 'No Chrome found'}

elif '${command}' == 'get_performance_insights':
    result = automation.get_insights()
    result['success'] = True

else:
    result = {'success': False, 'error': 'Unknown command'}

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
    console.error("Intelligent Control MCP Server running...");
  }
}

const server = new IntelligentControlMCP();
server.run().catch(console.error);

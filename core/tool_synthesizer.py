# ==========================================================
# JARVIS v11.0 GENESIS - Dynamic Tool Synthesis Engine
# JARVIS writes its own tools on-the-fly
# ==========================================================

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import json
import os
import subprocess
import ast
from typing import Set

_ALLOWED_AST_NODES: Set[type] = {
    ast.Module, ast.FunctionDef, ast.arguments, ast.arg, ast.Return,
    ast.Assign, ast.AnnAssign, ast.Expr, ast.If, ast.For, ast.While,
    ast.Break, ast.Continue, ast.Pass, ast.Try, ast.ExceptHandler,
    ast.Name, ast.Load, ast.Store, ast.Constant, ast.Dict, ast.List,
    ast.Tuple, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
    ast.Call, ast.Attribute, ast.Subscript, ast.Slice,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
    ast.Eq, ast.NotEq, ast.Gt, ast.GtE, ast.Lt, ast.LtE,
    ast.And, ast.Or, ast.Not
}

_ALLOWED_CALLS = {
    'len', 'str', 'int', 'float', 'bool', 'min', 'max', 'sum', 'sorted',
    'range', 'list', 'dict', 'set', 'tuple', 'abs', 'round'
}


def _is_ast_safe(code: str) -> bool:
    tree = ast.parse(code)
    for node in ast.walk(tree):
        if type(node) not in _ALLOWED_AST_NODES:
            return False

        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                if node.func.id not in _ALLOWED_CALLS:
                    return False
            elif isinstance(node.func, ast.Attribute):
                # Allow simple method calls on local objects; block dunder/system-like attrs
                if node.func.attr.startswith('__'):
                    return False
            else:
                return False

        if isinstance(node, ast.Attribute) and node.attr.startswith('__'):
            return False

    return True


def _execute_function_in_subprocess(code: str, input_data: dict):
    payload = json.dumps({'code': code, 'input': input_data})
    runner = (
        "import json,sys,ast; "
        "p=json.loads(sys.stdin.read()); "
        "code=p['code']; inp=p['input']; "
        "ns={}; "
        "exec(code, {'__builtins__': {'len':len,'str':str,'int':int,'float':float,'bool':bool,'min':min,'max':max,'sum':sum,'sorted':sorted,'range':range,'list':list,'dict':dict,'set':set,'tuple':tuple,'abs':abs,'round':round}}, ns); "
        "res=ns['execute'](inp); "
        "print(json.dumps({'ok': True, 'result': res}))"
    )

    proc = subprocess.run(
        ["python", "-c", runner],
        input=payload,
        capture_output=True,
        text=True,
        timeout=5
    )

    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or 'Subprocess execution failed')

    out = json.loads(proc.stdout.strip() or '{}')
    if not out.get('ok'):
        raise RuntimeError('Execution failed')

    return out.get('result')


def _execute_function_with_guard(code: str, input_data: dict):
    if not _is_ast_safe(code):
        raise ValueError('Generated code failed safety validation')

    return _execute_function_in_subprocess(code, input_data)




logger = logging.getLogger(__name__)


class DynamicToolSynthesizer:
    """
    Dynamic Tool Synthesis for JARVIS v11.0
    - Autonomous tool creation
    - MCP server generation
    - Tool testing framework
    - Permanent tool registration
    """

    def __init__(self):
        self.synthesized_tools = {}
        self.tool_registry = {}
        self.mcp_servers = {}

        logger.info("🔧 Dynamic Tool Synthesizer initialized")

    async def synthesize_tool(
        self,
        task_description: str,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
        llm_client = None
    ) -> Dict[str, Any]:
        """
        Synthesize a new tool for a specific task

        Args:
            task_description: What the tool should do
            input_schema: Expected input format
            output_schema: Expected output format
            llm_client: LLM client for code generation

        Returns:
            Tool details
        """
        logger.info(f"🛠️ Synthesizing tool for: {task_description[:50]}...")

        try:
            # Step 1: Generate tool code using LLM
            tool_code = await self._generate_tool_code(
                task_description,
                input_schema,
                output_schema,
                llm_client
            )

            # Step 2: Validate the generated code
            is_valid, validation_error = self._validate_code(tool_code)

            if not is_valid:
                logger.error(f"❌ Generated code is invalid: {validation_error}")
                return {"success": False, "error": validation_error}

            # Step 3: Test the tool
            test_result = await self._test_tool(tool_code, input_schema)

            if not test_result["success"]:
                logger.error(f"❌ Tool test failed: {test_result['error']}")
                return test_result

            # Step 4: Register the tool
            tool_id = f"tool_{hash(task_description + str(datetime.now()))}"
            tool_name = self._generate_tool_name(task_description)

            tool = {
                "id": tool_id,
                "name": tool_name,
                "description": task_description,
                "code": tool_code,
                "input_schema": input_schema,
                "output_schema": output_schema,
                "test_passed": True,
                "created_at": datetime.now().isoformat()
            }

            # Save tool to file
            tool_file = f"./tools/{tool_name}.py"
            os.makedirs("./tools", exist_ok=True)

            with open(tool_file, 'w') as f:
                f.write(tool_code)

            self.synthesized_tools[tool_id] = tool
            self.tool_registry[tool_name] = tool_file

            logger.info(f"✅ Tool synthesized: {tool_name}")

            return {
                "success": True,
                "tool": tool,
                "file": tool_file
            }

        except Exception as e:
            logger.error(f"❌ Tool synthesis failed: {e}")
            return {"success": False, "error": str(e)}

    async def _generate_tool_code(
        self,
        task_description: str,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any],
        llm_client
    ) -> str:
        """Generate Python code for the tool using LLM"""

        if not llm_client:
            # Fallback: Generate template code
            return self._generate_template_code(task_description, input_schema, output_schema)

        # Use LLM to generate code
        prompt = f"""Generate a Python function that does the following:

Task: {task_description}

Input Schema: {json.dumps(input_schema, indent=2)}
Output Schema: {json.dumps(output_schema, indent=2)}

Requirements:
1. Function should be named 'execute'
2. Include proper error handling
3. Add type hints
4. Include docstring
5. Return result matching output schema

Generate ONLY the Python code, no explanations."""

        try:
            response = llm_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a Python code generator. Generate clean, working code."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=1000
            )

            code = response.choices[0].message.content

            # Extract code from markdown if present
            if "```python" in code:
                code = code.split("```python")[1].split("```")[0].strip()
            elif "```" in code:
                code = code.split("```")[1].split("```")[0].strip()

            return code

        except Exception as e:
            logger.error(f"❌ LLM code generation failed: {e}")
            return self._generate_template_code(task_description, input_schema, output_schema)

    def _generate_template_code(
        self,
        task_description: str,
        input_schema: Dict[str, Any],
        output_schema: Dict[str, Any]
    ) -> str:
        """Generate template code when LLM is unavailable"""

        code = f'''"""
Auto-generated tool by JARVIS v11.0 GENESIS
Task: {task_description}
Generated: {datetime.now().isoformat()}
"""

from typing import Dict, Any

def execute(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    {task_description}

    Args:
        input_data: Input matching schema {list(input_schema.keys())}

    Returns:
        Output matching schema {list(output_schema.keys())}
    """
    try:
        # TODO: Implement actual logic
        # This is a template - needs LLM to generate real implementation

        result = {{}}
        for key in {list(output_schema.keys())}:
            result[key] = None

        return {{"success": True, "result": result}}

    except Exception as e:
        return {{"success": False, "error": str(e)}}
'''

        return code

    def _validate_code(self, code: str) -> tuple:
        """Validate Python code syntax"""
        try:
            ast.parse(code)
            return True, None
        except SyntaxError as e:
            return False, f"Syntax error: {str(e)}"

    async def _test_tool(self, code: str, input_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Test the generated tool with sample input"""
        try:
            # Create test input
            test_input = {}
            for key, value_type in input_schema.items():
                if value_type == "string":
                    test_input[key] = "test"
                elif value_type == "number":
                    test_input[key] = 42
                elif value_type == "boolean":
                    test_input[key] = True
                else:
                    test_input[key] = None

            # Execute code with AST safety validation + subprocess isolation
            result = _execute_function_with_guard(code, test_input)

            logger.info(f"✅ Tool test passed")

            return {"success": True, "test_result": result}

        except Exception as e:
            logger.error(f"❌ Tool test failed: {e}")
            return {"success": False, "error": str(e)}

    def _generate_tool_name(self, task_description: str) -> str:
        """Generate a valid Python function name from task description"""
        # Convert to snake_case
        name = task_description.lower()
        name = ''.join(c if c.isalnum() or c.isspace() else '' for c in name)
        name = '_'.join(name.split())
        name = name[:50]  # Limit length

        return name

    async def create_mcp_server(
        self,
        tool_id: str,
        port: int = 5000
    ) -> Dict[str, Any]:
        """
        Wrap a synthesized tool in an MCP server

        Args:
            tool_id: ID of synthesized tool
            port: Port for MCP server

        Returns:
            MCP server details
        """
        if tool_id not in self.synthesized_tools:
            return {"success": False, "error": "Tool not found"}

        tool = self.synthesized_tools[tool_id]

        logger.info(f"🌐 Creating MCP server for: {tool['name']}")

        try:
            # Generate MCP server code
            mcp_code = f'''"""
MCP Server for {tool['name']}
Auto-generated by JARVIS v11.0 GENESIS
"""

from flask import Flask, request, jsonify
import sys
sys.path.append('./tools')

from {tool['name']} import execute

app = Flask(__name__)

@app.route('/execute', methods=['POST'])
def handle_execute():
    try:
        input_data = request.json
        result = execute(input_data)
        return jsonify(result)
    except Exception as e:
        return jsonify({{"success": False, "error": str(e)}}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({{"status": "healthy", "tool": "{tool['name']}"}})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port={port})
'''

            # Save MCP server
            mcp_file = f"./mcp/{tool['name']}_server.py"
            os.makedirs("./mcp", exist_ok=True)

            with open(mcp_file, 'w') as f:
                f.write(mcp_code)

            mcp_server = {
                "id": f"mcp_{tool_id}",
                "tool_id": tool_id,
                "tool_name": tool['name'],
                "port": port,
                "file": mcp_file,
                "status": "created",
                "created_at": datetime.now().isoformat()
            }

            self.mcp_servers[mcp_server["id"]] = mcp_server

            logger.info(f"✅ MCP server created: {mcp_file}")

            return {
                "success": True,
                "mcp_server": mcp_server
            }

        except Exception as e:
            logger.error(f"❌ MCP server creation failed: {e}")
            return {"success": False, "error": str(e)}

    async def start_mcp_server(self, mcp_id: str) -> Dict[str, Any]:
        """Start an MCP server"""
        if mcp_id not in self.mcp_servers:
            return {"success": False, "error": "MCP server not found"}

        mcp = self.mcp_servers[mcp_id]

        logger.info(f"🚀 Starting MCP server: {mcp['tool_name']}")

        try:
            # Start server in background
            process = subprocess.Popen(
                ["python", mcp["file"]],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )

            mcp["process_id"] = process.pid
            mcp["status"] = "running"

            logger.info(f"✅ MCP server running on port {mcp['port']} (PID: {process.pid})")

            return {
                "success": True,
                "mcp_server": mcp
            }

        except Exception as e:
            logger.error(f"❌ Failed to start MCP server: {e}")
            return {"success": False, "error": str(e)}

    def get_tool_registry(self) -> Dict[str, Any]:
        """Get all synthesized tools"""
        return {
            "total_tools": len(self.synthesized_tools),
            "total_mcp_servers": len(self.mcp_servers),
            "tools": list(self.synthesized_tools.values()),
            "mcp_servers": list(self.mcp_servers.values())
        }


# Test
if __name__ == "__main__":
    import asyncio

    async def test_tool_synthesizer():
        synthesizer = DynamicToolSynthesizer()

        print("\n" + "="*50)
        print("DYNAMIC TOOL SYNTHESIZER TEST")
        print("="*50)

        # Test 1: Synthesize a tool
        print("\n1. Synthesizing tool...")
        tool = await synthesizer.synthesize_tool(
            task_description="Convert temperature from Celsius to Fahrenheit",
            input_schema={"celsius": "number"},
            output_schema={"fahrenheit": "number"},
            llm_client=None  # Will use template
        )
        print(f"Result: {tool['success']}")
        if tool['success']:
            print(f"Tool file: {tool['file']}")

        # Test 2: Create MCP server
        if tool['success']:
            print("\n2. Creating MCP server...")
            mcp = await synthesizer.create_mcp_server(
                tool_id=tool['tool']['id'],
                port=5001
            )
            print(f"Result: {mcp}")

        # Test 3: Get registry
        print("\n3. Tool Registry:")
        registry = synthesizer.get_tool_registry()
        print(json.dumps(registry, indent=2))

    asyncio.run(test_tool_synthesizer())

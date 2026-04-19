"""
==========================================================
JARVIS - Code Mutator (Evolutionary Biology)
==========================================================
Generates optimized code variants using LLM.
Uses AST to surgically replace functions.
==========================================================
"""

import ast
import inspect
import logging
import os
from typing import Callable, Optional, Dict, Any
from core.llm_provider import LLMProvider

logger = logging.getLogger(__name__)

class CodeMutator:
    def __init__(self):
        self.llm = LLMProvider.instance()

    async def mutate_function(self, func: Callable, strategy: str) -> Optional[str]:
        """
        Generate an optimized version of a function.
        Returns the source code of the new version.
        """
        try:
            source = inspect.getsource(func)

            prompt = f"""
            You are an Evolutionary Code Optimizer for the JARVIS system.
            Optimize the following Python function using the strategy: {strategy}.

            ORIGINAL SOURCE:
            {source}

            STRATEGY DETAILS:
            - If CACHING: Add lru_cache or custom dict cache.
            - If ASYNC: Convert to async/await if I/O bound.
            - If PARALLEL: Use ProcessPool or ThreadPool.
            - If BATCHING: Combine multiple similar calls into one.

            RULES:
            1. Maintain exact signature and logic.
            2. Only change implementation for performance.
            3. Return ONLY the code for the function. No preamble, no markdown fences.
            4. Include all necessary imports within the function or at the top of the block.
            """

            logger.info(f"🧬 Mutating {func.__name__} with strategy {strategy}")

            response = await self.llm.generate(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.2
            )

            new_source = response.get("text", "").strip()
            if "def " in new_source:
                return new_source
            return None

        except Exception as e:
            logger.error(f"❌ Mutation failed: {e}")
            return None

    def apply_mutation(self, original_file: str, func_name: str, new_source: str):
        """Surgically replace a function in a file"""
        try:
            with open(original_file, 'r') as f:
                lines = f.readlines()

            # Use AST to find line numbers
            tree = ast.parse("".join(lines))
            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == func_name:
                    start = node.lineno - 1
                    end = node.end_lineno

                    # Replace lines
                    new_lines = lines[:start] + [new_source + "\n"] + lines[end:]

                    with open(original_file, 'w') as f:
                        f.writelines(new_lines)
                    logger.info(f"✅ Mutation applied to {original_file}:{func_name}")
                    return True
            return False
        except Exception as e:
            logger.error(f"❌ Failed to apply mutation: {e}")
            return False

mutator = CodeMutator()

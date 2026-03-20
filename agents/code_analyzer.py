# ==========================================================
# Sub-Agent: CodeAnalyzer
# Analyzes code, finds bugs, suggests improvements
# ==========================================================

import logging
from typing import Dict, Any, List
import ast
import re

logger = logging.getLogger(__name__)


class CodeAnalyzerAgent:
    """
    Specialized agent for code analysis
    - Bug detection
    - Code review
    - Pattern analysis
    - Complexity metrics
    """

    def __init__(self):
        self.name = "CodeAnalyzer"
        self.role = "code_analysis"
        self.risk_level = 2
        logger.info(f"🔍 {self.name} initialized")

    async def analyze(self, code: str, language: str = "python") -> Dict[str, Any]:
        """
        Analyze code and return findings

        Args:
            code: Source code to analyze
            language: Programming language

        Returns:
            Analysis results
        """
        logger.info(f"🔍 Analyzing {language} code...")

        results = {
            "bugs": [],
            "warnings": [],
            "suggestions": [],
            "metrics": {},
            "score": 0
        }

        if language == "python":
            results = await self._analyze_python(code)
        elif language == "javascript":
            results = await self._analyze_javascript(code)

        logger.info(f"✅ Analysis complete: {len(results['bugs'])} bugs, {len(results['warnings'])} warnings")

        return results

    async def _analyze_python(self, code: str) -> Dict[str, Any]:
        """Analyze Python code"""
        results = {
            "bugs": [],
            "warnings": [],
            "suggestions": [],
            "metrics": {},
            "score": 100
        }

        try:
            # Parse AST
            tree = ast.parse(code)

            # Check for common issues
            results["bugs"].extend(self._check_undefined_variables(tree))
            results["warnings"].extend(self._check_complexity(tree))
            results["suggestions"].extend(self._check_best_practices(tree))

            # Calculate metrics
            results["metrics"] = {
                "lines": len(code.split('\n')),
                "functions": len([n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]),
                "classes": len([n for n in ast.walk(tree) if isinstance(n, ast.ClassDef)])
            }

            # Calculate score
            results["score"] = max(0, 100 - len(results["bugs"]) * 10 - len(results["warnings"]) * 5)

        except SyntaxError as e:
            results["bugs"].append({
                "type": "syntax_error",
                "message": str(e),
                "line": e.lineno,
                "severity": "critical"
            })
            results["score"] = 0

        return results

    def _check_undefined_variables(self, tree) -> List[Dict]:
        """Check for undefined variables"""
        issues = []
        # Simplified check - in production use proper scope analysis
        return issues

    def _check_complexity(self, tree) -> List[Dict]:
        """Check code complexity"""
        warnings = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Count nested levels
                depth = self._get_nesting_depth(node)
                if depth > 4:
                    warnings.append({
                        "type": "high_complexity",
                        "message": f"Function '{node.name}' has high nesting depth: {depth}",
                        "line": node.lineno,
                        "severity": "warning"
                    })

        return warnings

    def _check_best_practices(self, tree) -> List[Dict]:
        """Check for best practices"""
        suggestions = []

        for node in ast.walk(tree):
            # Check for bare except
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                suggestions.append({
                    "type": "bare_except",
                    "message": "Use specific exception types instead of bare 'except'",
                    "line": node.lineno,
                    "severity": "info"
                })

        return suggestions

    def _get_nesting_depth(self, node, depth=0) -> int:
        """Calculate nesting depth"""
        max_depth = depth
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With)):
                child_depth = self._get_nesting_depth(child, depth + 1)
                max_depth = max(max_depth, child_depth)
        return max_depth

    async def _analyze_javascript(self, code: str) -> Dict[str, Any]:
        """Analyze JavaScript code"""
        results = {
            "bugs": [],
            "warnings": [],
            "suggestions": [],
            "metrics": {
                "lines": len(code.split('\n'))
            },
            "score": 100
        }

        # Basic checks for JavaScript
        if "var " in code:
            results["suggestions"].append({
                "type": "use_let_const",
                "message": "Use 'let' or 'const' instead of 'var'",
                "severity": "info"
            })

        if "==" in code and "===" not in code:
            results["warnings"].append({
                "type": "loose_equality",
                "message": "Use '===' instead of '=='",
                "severity": "warning"
            })

        return results


# Test
if __name__ == "__main__":
    import asyncio

    async def test():
        agent = CodeAnalyzerAgent()

        # Test Python code
        python_code = """
def complex_function(x):
    if x > 0:
        if x > 10:
            if x > 20:
                if x > 30:
                    if x > 40:
                        return "very high"
    try:
        result = x / 0
    except:
        pass
    return "low"
"""

        result = await agent.analyze(python_code, "python")

        print("\n" + "="*50)
        print("CODE ANALYSIS RESULTS")
        print("="*50)
        print(f"Score: {result['score']}/100")
        print(f"\nBugs: {len(result['bugs'])}")
        for bug in result['bugs']:
            print(f"  - {bug['message']}")

        print(f"\nWarnings: {len(result['warnings'])}")
        for warning in result['warnings']:
            print(f"  - {warning['message']}")

        print(f"\nSuggestions: {len(result['suggestions'])}")
        for suggestion in result['suggestions']:
            print(f"  - {suggestion['message']}")

    asyncio.run(test())

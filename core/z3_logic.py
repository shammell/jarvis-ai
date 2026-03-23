# ==========================================================
# JARVIS v11.0 - Z3 Logic Utilities
# Zero-hallucination Z3 theorem prover utilities
# ==========================================================

import logging
from typing import Dict, Any, List, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class Z3LogicUtilities:
    """
    Z3 Logic Utilities for JARVIS v11.0
    - Safe Z3 operations
    - Constraint parsing utilities
    - Theorem proving helpers
    """

    def __init__(self):
        self.z3_available = False
        self.z3 = None

        self._init_z3()

    def _init_z3(self):
        """Initialize Z3 theorem prover"""
        try:
            import z3
            self.z3 = z3
            self.z3_available = True
            logger.info("✅ Z3 Logic Utilities initialized")
        except ImportError:
            logger.warning("⚠️ Z3 not available. Install: pip install z3-solver")

    def parse_numeric_constraints(self, statement: str) -> Dict[str, Any]:
        """
        Parse simple numeric constraints from natural language

        Args:
            statement: Natural language statement with constraints

        Returns:
            Parsed constraints or error
        """
        if not self.z3_available:
            return {
                "success": False,
                "error": "Z3 not available",
                "parsed": False
            }

        try:
            import re

            # Extract variables and constraints
            # Pattern: variable >/< value, variable == value, etc.
            patterns = {
                "greater_than": r'(\w+)\s*>\s*(\d+)',
                "less_than": r'(\w+)\s*<\s*(\d+)',
                "equal": r'(\w+)\s*==?\s*(\d+)',
                "greater_equal": r'(\w+)\s*>=\s*(\d+)',
                "less_equal": r'(\w+)\s*<=\s*(\d+)',
            }

            constraints = []
            variables = set()

            for constraint_type, pattern in patterns.items():
                matches = re.findall(pattern, statement)
                for var, value in matches:
                    variables.add(var)
                    constraints.append({
                        "type": constraint_type,
                        "variable": var,
                        "value": int(value)
                    })

            return {
                "success": True,
                "variables": list(variables),
                "constraints": constraints,
                "parsed": len(constraints) > 0
            }

        except Exception as e:
            logger.error(f"Failed to parse constraints: {e}")
            return {
                "success": False,
                "error": str(e),
                "parsed": False
            }

    def create_z3_solver(self, constraints: List[Dict[str, Any]]) -> Optional[Any]:
        """
        Create Z3 solver with parsed constraints

        Args:
            constraints: List of parsed constraints

        Returns:
            Z3 solver or None
        """
        if not self.z3_available or not constraints:
            return None

        try:
            solver = self.z3.Solver()
            variables = {}

            # Create Z3 variables
            for constraint in constraints:
                var_name = constraint["variable"]
                if var_name not in variables:
                    variables[var_name] = self.z3.Int(var_name)

            # Add constraints to solver
            for constraint in constraints:
                var = variables[constraint["variable"]]
                value = self.z3.IntVal(constraint["value"])

                if constraint["type"] == "greater_than":
                    solver.add(var > value)
                elif constraint["type"] == "less_than":
                    solver.add(var < value)
                elif constraint["type"] == "equal":
                    solver.add(var == value)
                elif constraint["type"] == "greater_equal":
                    solver.add(var >= value)
                elif constraint["type"] == "less_equal":
                    solver.add(var <= value)

            return solver

        except Exception as e:
            logger.error(f"Failed to create Z3 solver: {e}")
            return None

    def check_satisfiability(self, solver) -> Dict[str, Any]:
        """
        Check satisfiability of Z3 solver

        Args:
            solver: Z3 solver

        Returns:
            Satisfiability result
        """
        if not self.z3_available or solver is None:
            return {
                "success": False,
                "error": "Z3 not available or solver invalid",
                "satisfiable": False,
                "result": None
            }

        try:
            result = solver.check()

            is_satisfiable = (result == self.z3.sat)
            model = None

            if is_satisfiable:
                model = solver.model()

            return {
                "success": True,
                "satisfiable": is_satisfiable,
                "result": str(result),
                "model": str(model) if model else None
            }

        except Exception as e:
            logger.error(f"Z3 satisfiability check failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "satisfiable": False,
                "result": None
            }

    def verify_simple_logic(self, statement: str) -> Dict[str, Any]:
        """
        Verify simple logic statement with numeric constraints

        Args:
            statement: Logic statement

        Returns:
            Verification result
        """
        if not self.z3_available:
            return {
                "success": False,
                "error": "Z3 not available",
                "verified": False,
                "satisfiable": False
            }

        try:
            # Parse constraints
            parse_result = self.parse_numeric_constraints(statement)

            if not parse_result["success"] or not parse_result["parsed"]:
                return {
                    "success": False,
                    "error": "No numeric constraints found or parsing failed",
                    "verified": False,
                    "satisfiable": False,
                    "statement": statement
                }

            # Create solver
            solver = self.create_z3_solver(parse_result["constraints"])

            if solver is None:
                return {
                    "success": False,
                    "error": "Failed to create Z3 solver",
                    "verified": False,
                    "satisfiable": False
                }

            # Check satisfiability
            check_result = self.check_satisfiability(solver)

            return {
                "success": True,
                "verified": True,
                "satisfiable": check_result["satisfiable"],
                "result": check_result["result"],
                "model": check_result["model"],
                "statement": statement,
                "parsed_constraints": parse_result["constraints"],
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Logic verification failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "verified": False,
                "satisfiable": False,
                "statement": statement
            }


# Test
if __name__ == "__main__":
    import asyncio

    async def test_z3_logic():
        z3_utils = Z3LogicUtilities()

        print("\n" + "="*50)
        print("Z3 LOGIC UTILITIES TEST")
        print("="*50)

        # Test 1: Parse constraints
        print("\n1. Parsing constraints...")
        statement = "x > 5 and x < 10"
        parse_result = z3_utils.parse_numeric_constraints(statement)
        print(f"Statement: {statement}")
        print(f"Result: {parse_result}")

        # Test 2: Create solver and check
        print("\n2. Creating solver and checking satisfiability...")
        if parse_result["success"] and parse_result["parsed"]:
            solver = z3_utils.create_z3_solver(parse_result["constraints"])
            if solver:
                check_result = z3_utils.check_satisfiability(solver)
                print(f"Satisfiability: {check_result}")
            else:
                print("Failed to create solver")

        # Test 3: Full verification
        print("\n3. Full logic verification...")
        verification = z3_utils.verify_simple_logic("x > 5 and x < 10")
        print(f"Verification: {verification}")

        # Test 4: Unsatisfiable case
        print("\n4. Testing unsatisfiable case...")
        unsat_verification = z3_utils.verify_simple_logic("x > 10 and x < 5")
        print(f"Unsatisfiable verification: {unsat_verification}")

    asyncio.run(test_z3_logic())
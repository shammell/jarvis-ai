# ==========================================================
# JARVIS v9.0 - First Principles Reasoning Engine
# Break down problems to fundamental truths, rebuild from scratch
# Challenge assumptions at every step
# ==========================================================

import logging
from typing import List, Dict, Any, Optional
import os

try:
    from groq import Groq
except ImportError:
    Groq = None

logger = logging.getLogger(__name__)


class FirstPrinciples:
    """
    First-principles reasoning engine
    - Decompose problems into axioms
    - Challenge all assumptions
    - Rebuild solutions from ground truth
    - Elon Musk-style thinking
    """

    def __init__(self, groq_api_key: str = None):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.groq_api_key) if Groq and self.groq_api_key else None
        self.model = "llama-3.3-70b-versatile"

        logger.info("🔬 First Principles Engine initialized")

    def decompose(self, problem: str, context: str = "") -> Dict[str, Any]:
        """
        Decompose problem into first principles

        Args:
            problem: The problem to decompose
            context: Additional context

        Returns:
            {
                axioms: List[str],
                assumptions: List[str],
                constraints: List[str],
                solution: str,
                reasoning: str
            }
        """
        if not self.client:
            logger.error("❌ Groq client not initialized")
            return self._fallback_decomposition(problem)

        logger.info(f"🔬 Decomposing: {problem[:50]}...")

        try:
            # Step 1: Identify assumptions
            assumptions = self._identify_assumptions(problem, context)

            # Step 2: Extract axioms (fundamental truths)
            axioms = self._extract_axioms(problem, context, assumptions)

            # Step 3: Identify constraints
            constraints = self._identify_constraints(problem, context)

            # Step 4: Rebuild solution from axioms
            solution = self._rebuild_solution(problem, axioms, constraints)

            # Step 5: Generate reasoning explanation
            reasoning = self._generate_reasoning(problem, axioms, assumptions, constraints, solution)

            logger.info("✅ First principles decomposition complete")

            return {
                "axioms": axioms,
                "assumptions": assumptions,
                "constraints": constraints,
                "solution": solution,
                "reasoning": reasoning
            }

        except Exception as e:
            logger.error(f"❌ Decomposition failed: {e}")
            return self._fallback_decomposition(problem)

    def _identify_assumptions(self, problem: str, context: str) -> List[str]:
        """Identify hidden assumptions in the problem"""
        prompt = f"""Identify ALL assumptions (explicit and implicit) in this problem.
Challenge every assumption. What are we taking for granted?

Problem: {problem}
Context: {context}

List assumptions as bullet points. Be thorough and critical."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a critical thinker who challenges all assumptions."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )

            text = response.choices[0].message.content
            assumptions = [line.strip('- ').strip() for line in text.split('\n') if line.strip().startswith('-')]

            logger.info(f"📋 Identified {len(assumptions)} assumptions")
            return assumptions

        except Exception as e:
            logger.error(f"❌ Assumption identification failed: {e}")
            return ["Unable to identify assumptions"]

    def _extract_axioms(self, problem: str, context: str, assumptions: List[str]) -> List[str]:
        """Extract fundamental truths (axioms)"""
        prompt = f"""Break this problem down to FUNDAMENTAL TRUTHS (axioms).
What are the absolute, undeniable facts? Strip away all assumptions and conventions.

Problem: {problem}
Context: {context}
Assumptions to challenge: {', '.join(assumptions)}

List only fundamental truths that cannot be further reduced. Be rigorous."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a physicist who thinks from first principles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2,
                max_tokens=500
            )

            text = response.choices[0].message.content
            axioms = [line.strip('- ').strip() for line in text.split('\n') if line.strip().startswith('-')]

            logger.info(f"🔬 Extracted {len(axioms)} axioms")
            return axioms

        except Exception as e:
            logger.error(f"❌ Axiom extraction failed: {e}")
            return ["Unable to extract axioms"]

    def _identify_constraints(self, problem: str, context: str) -> List[str]:
        """Identify real constraints (not artificial limitations)"""
        prompt = f"""Identify REAL constraints (physics, resources, time, etc.).
Ignore artificial constraints imposed by convention or tradition.

Problem: {problem}
Context: {context}

List only genuine, unavoidable constraints."""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You distinguish between real and artificial constraints."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=300
            )

            text = response.choices[0].message.content
            constraints = [line.strip('- ').strip() for line in text.split('\n') if line.strip().startswith('-')]

            logger.info(f"⚙️ Identified {len(constraints)} constraints")
            return constraints

        except Exception as e:
            logger.error(f"❌ Constraint identification failed: {e}")
            return ["Unable to identify constraints"]

    def _rebuild_solution(self, problem: str, axioms: List[str], constraints: List[str]) -> str:
        """Rebuild solution from axioms, respecting only real constraints"""
        prompt = f"""Now rebuild the solution from FIRST PRINCIPLES.
Use ONLY the axioms and real constraints. Ignore all conventions and "how it's always been done."

Problem: {problem}

Axioms (fundamental truths):
{chr(10).join(f'- {a}' for a in axioms)}

Real constraints:
{chr(10).join(f'- {c}' for c in constraints)}

Design the optimal solution from scratch. Think like Elon Musk: what's the physics-based best approach?"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an innovative engineer who rebuilds from first principles."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=800
            )

            solution = response.choices[0].message.content
            logger.info("✅ Solution rebuilt from first principles")
            return solution

        except Exception as e:
            logger.error(f"❌ Solution rebuild failed: {e}")
            return "Unable to rebuild solution"

    def _generate_reasoning(
        self,
        problem: str,
        axioms: List[str],
        assumptions: List[str],
        constraints: List[str],
        solution: str
    ) -> str:
        """Generate explanation of the reasoning process"""
        reasoning = f"""# First Principles Analysis

## Original Problem
{problem}

## Assumptions Challenged
{chr(10).join(f'- {a}' for a in assumptions)}

## Fundamental Truths (Axioms)
{chr(10).join(f'- {a}' for a in axioms)}

## Real Constraints
{chr(10).join(f'- {c}' for c in constraints)}

## Solution from First Principles
{solution}

---
This solution was derived by:
1. Challenging all assumptions
2. Reducing to fundamental truths
3. Identifying only real constraints
4. Rebuilding from ground truth
"""
        return reasoning

    def _fallback_decomposition(self, problem: str) -> Dict[str, Any]:
        """Fallback when LLM unavailable"""
        return {
            "axioms": ["LLM unavailable for decomposition"],
            "assumptions": ["Unable to identify"],
            "constraints": ["Unable to identify"],
            "solution": "First principles analysis requires LLM",
            "reasoning": "System unavailable"
        }

    def analyze_why(self, question: str, depth: int = 3) -> str:
        """
        Recursive "why" analysis (5 Whys technique)

        Args:
            question: The "why" question
            depth: How many levels deep to go

        Returns:
            Analysis string
        """
        if not self.client:
            return "LLM unavailable"

        logger.info(f"❓ Analyzing why: {question[:50]}...")

        analysis = f"# Why Analysis\n\n**Question:** {question}\n\n"
        current_question = question

        for i in range(depth):
            try:
                prompt = f"Why is this true? Give a fundamental reason, not a surface explanation.\n\n{current_question}"

                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You explain root causes, not symptoms."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=200
                )

                answer = response.choices[0].message.content
                analysis += f"**Why {i+1}:** {answer}\n\n"
                current_question = f"Why {answer}?"

            except Exception as e:
                logger.error(f"❌ Why analysis failed at depth {i+1}: {e}")
                break

        logger.info(f"✅ Why analysis complete ({depth} levels)")
        return analysis


# Test
if __name__ == "__main__":
    fp = FirstPrinciples()

    problem = """
    We need to build a faster WhatsApp bot. Currently using Puppeteer which uses 500MB RAM.
    How can we make it faster?
    """

    print("\n" + "="*50)
    print("FIRST PRINCIPLES DECOMPOSITION")
    print("="*50)

    result = fp.decompose(problem)

    print("\n🔬 AXIOMS:")
    for axiom in result['axioms']:
        print(f"  - {axiom}")

    print("\n📋 ASSUMPTIONS:")
    for assumption in result['assumptions']:
        print(f"  - {assumption}")

    print("\n⚙️ CONSTRAINTS:")
    for constraint in result['constraints']:
        print(f"  - {constraint}")

    print("\n💡 SOLUTION:")
    print(result['solution'])

    print("\n" + "="*50)
    print("WHY ANALYSIS")
    print("="*50)

    why_result = fp.analyze_why("Why does Puppeteer use so much RAM?", depth=3)
    print(why_result)

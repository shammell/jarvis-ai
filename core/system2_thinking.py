# ==========================================================
# JARVIS v9.0 - System 2 Thinking (Test-Time Compute)
# Monte Carlo Tree Search + Process Reward Model
# Similar to OpenAI o1/o3 approach
# ==========================================================

import logging
from typing import List, Dict, Any, Optional, Tuple
import time
import random
import math
import os

try:
    from groq import Groq
except ImportError:
    Groq = None

logger = logging.getLogger(__name__)


class MCTSNode:
    """Node in Monte Carlo Tree Search"""

    def __init__(self, state: str, parent=None, action: str = ""):
        self.state = state  # Current reasoning state
        self.parent = parent
        self.action = action  # Action that led to this state
        self.children = []
        self.visits = 0
        self.value = 0.0
        self.untried_actions = []

    def is_fully_expanded(self) -> bool:
        return len(self.untried_actions) == 0

    def best_child(self, exploration_weight: float = 1.414) -> 'MCTSNode':
        """Select best child using UCB1"""
        choices_weights = [
            (child.value / child.visits) + exploration_weight * math.sqrt(math.log(self.visits) / child.visits)
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]

    def add_child(self, state: str, action: str) -> 'MCTSNode':
        """Add a child node"""
        child = MCTSNode(state, parent=self, action=action)
        self.children.append(child)
        return child


class System2Thinking:
    """
    System 2 thinking for complex reasoning
    - Uses MCTS to explore solution space
    - Self-evaluates each path with Process Reward Model
    - Returns best path after N iterations
    """

    def __init__(self, groq_api_key: str = None):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.groq_api_key) if Groq and self.groq_api_key else None

        self.model = "llama-3.3-70b-versatile"
        self.max_iterations = 10
        self.max_depth = 5

        logger.info("🧠 System 2 Thinking initialized")

    def reason(
        self,
        problem: str,
        context: str = "",
        max_iterations: int = None,
        max_depth: int = None
    ) -> Dict[str, Any]:
        """
        Deep reasoning using MCTS + PRM

        Args:
            problem: The problem to solve
            context: Additional context
            max_iterations: Number of MCTS iterations
            max_depth: Maximum reasoning depth

        Returns:
            {solution: str, reasoning_path: List[str], confidence: float, time_ms: int}
        """
        if not self.client:
            logger.error("❌ Groq client not initialized")
            return {"solution": "", "reasoning_path": [], "confidence": 0.0, "time_ms": 0}

        start_time = time.time()
        max_iterations = max_iterations or self.max_iterations
        max_depth = max_depth or self.max_depth

        logger.info(f"🧠 Starting System 2 reasoning: {problem[:50]}...")

        # Initialize MCTS root
        initial_state = f"Problem: {problem}\nContext: {context}\n\nLet me think step by step:"
        root = MCTSNode(state=initial_state)

        # Generate initial possible actions
        root.untried_actions = self._generate_actions(initial_state, problem)

        # MCTS iterations
        best_node = root
        best_value = -float('inf')

        for iteration in range(max_iterations):
            logger.info(f"🔄 MCTS iteration {iteration + 1}/{max_iterations}")

            # Selection
            node = self._select(root)

            # Expansion
            if not node.is_fully_expanded() and node.visits > 0:
                node = self._expand(node, problem)

            # Simulation
            value = self._simulate(node, problem, max_depth)

            # Backpropagation
            self._backpropagate(node, value)

            # Track best node
            if value > best_value:
                best_value = value
                best_node = node

        # Extract best reasoning path
        reasoning_path = self._extract_path(best_node)
        solution = reasoning_path[-1] if reasoning_path else ""

        elapsed_ms = int((time.time() - start_time) * 1000)

        logger.info(f"✅ System 2 reasoning complete in {elapsed_ms}ms (confidence: {best_value:.2f})")

        return {
            "solution": solution,
            "reasoning_path": reasoning_path,
            "confidence": best_value,
            "time_ms": elapsed_ms,
            "iterations": max_iterations
        }

    def _select(self, node: MCTSNode) -> MCTSNode:
        """Select a node to expand using UCB1"""
        while node.children:
            if not node.is_fully_expanded():
                return node
            node = node.best_child()
        return node

    def _expand(self, node: MCTSNode, problem: str) -> MCTSNode:
        """Expand node by trying an untried action"""
        if not node.untried_actions:
            return node

        action = node.untried_actions.pop()
        new_state = self._apply_action(node.state, action, problem)
        child = node.add_child(new_state, action)

        # Generate actions for child
        child.untried_actions = self._generate_actions(new_state, problem)

        return child

    def _simulate(self, node: MCTSNode, problem: str, max_depth: int) -> float:
        """Simulate reasoning from node and evaluate with PRM"""
        current_state = node.state
        depth = 0

        # Simulate reasoning steps
        while depth < max_depth:
            # Generate next reasoning step
            next_step = self._generate_reasoning_step(current_state, problem)
            if not next_step or "FINAL ANSWER:" in next_step:
                break

            current_state += f"\n{next_step}"
            depth += 1

        # Evaluate with Process Reward Model
        value = self._evaluate_reasoning(current_state, problem)

        return value

    def _backpropagate(self, node: MCTSNode, value: float):
        """Backpropagate value up the tree"""
        while node:
            node.visits += 1
            node.value += value
            node = node.parent

    def _generate_actions(self, state: str, problem: str) -> List[str]:
        """Generate possible reasoning actions"""
        actions = [
            "Break down the problem into smaller parts",
            "Consider alternative approaches",
            "Analyze assumptions and constraints",
            "Apply first principles thinking",
            "Look for patterns or analogies",
            "Verify the logic so far"
        ]
        return actions

    def _apply_action(self, state: str, action: str, problem: str) -> str:
        """Apply reasoning action to generate new state"""
        try:
            prompt = f"{state}\n\nAction: {action}\n\nContinue reasoning:"

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a logical reasoning assistant. Think step by step."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=200,
                temperature=0.7
            )

            new_reasoning = response.choices[0].message.content
            return state + f"\n\n{action}: {new_reasoning}"

        except Exception as e:
            logger.error(f"❌ Action application failed: {e}")
            return state

    def _generate_reasoning_step(self, state: str, problem: str) -> str:
        """Generate next reasoning step"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "Continue the reasoning. Be concise."},
                    {"role": "user", "content": state}
                ],
                max_tokens=100,
                temperature=0.7
            )

            return response.choices[0].message.content

        except Exception as e:
            logger.error(f"❌ Reasoning step failed: {e}")
            return ""

    def _evaluate_reasoning(self, reasoning: str, problem: str) -> float:
        """
        Process Reward Model: Evaluate quality of reasoning
        Returns: Score between 0.0 and 1.0
        """
        try:
            prompt = f"""Evaluate the quality of this reasoning for solving the problem.
Score from 0.0 (poor) to 1.0 (excellent).

Problem: {problem}

Reasoning:
{reasoning}

Evaluation criteria:
- Logical consistency
- Completeness
- Correctness
- Clarity

Return only a number between 0.0 and 1.0."""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a reasoning evaluator. Return only a number."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=10,
                temperature=0.1
            )

            score_text = response.choices[0].message.content.strip()
            score = float(score_text)
            return max(0.0, min(1.0, score))

        except Exception as e:
            logger.error(f"❌ Evaluation failed: {e}")
            return 0.5  # Default neutral score

    def _extract_path(self, node: MCTSNode) -> List[str]:
        """Extract reasoning path from root to node"""
        path = []
        current = node

        while current:
            if current.action:
                path.append(f"{current.action}: {current.state.split(current.action)[-1].strip()[:200]}")
            current = current.parent

        return list(reversed(path))


# Test
if __name__ == "__main__":
    system2 = System2Thinking()

    problem = """
    A farmer has 17 sheep. All but 9 die. How many sheep are left?
    """

    print("\n" + "="*50)
    print("SYSTEM 2 THINKING TEST")
    print("="*50)

    result = system2.reason(problem, max_iterations=5, max_depth=3)

    print(f"\n✅ Solution: {result['solution']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Time: {result['time_ms']}ms")

    print("\n📝 Reasoning Path:")
    for i, step in enumerate(result['reasoning_path'], 1):
        print(f"{i}. {step[:150]}...")

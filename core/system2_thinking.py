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
import asyncio
from concurrent.futures import ThreadPoolExecutor
from threading import Lock, RLock
import weakref

from core.security_system import input_validator
from core.resilience_patterns import resilience_manager, CircuitBreaker, Bulkhead, WatchdogTimer, ResourcePool
from core.experience_replay import experience_replay
from memory.memory_controller import MemoryController

MAX_PROBLEM_CHARS = 10000
MAX_CONTEXT_CHARS = 20000
MAX_MCTS_ITERATIONS = 50
MAX_MCTS_DEPTH = 10
MAX_STATE_CHARS = 60000
MAX_EVAL_CHARS = 20000

try:
    from groq import Groq
except ImportError:
    Groq = None

logger = logging.getLogger(__name__)


class MCTSNode:
    """Node in Monte Carlo Tree Search - Concurrency-safe with bounded resources"""

    # Class-level resource pool for nodes to prevent unbounded memory allocation
    _resource_pool = resilience_manager.get_resource_pool("mcts_node_pool", max_size=1000)

    def __init__(self, state: str, parent=None, action: str = ""):
        self.state = state  # Current reasoning state
        self.parent = parent
        self.action = action  # Action that led to this state
        self.children = []
        self.visits = 0
        self.value = 0.0
        self.untried_actions = []

        # Concurrency safety - each node has its own lock for thread safety
        self._lock = RLock()  # Reentrant lock for operations within the node

        # Track children safely to prevent race conditions during expansion
        self._child_lock = Lock()

    def is_fully_expanded(self) -> bool:
        with self._lock:
            return len(self.untried_actions) == 0

    def best_child(self, exploration_weight: float = 1.414) -> 'MCTSNode':
        """Select best child using UCB1 + Experience Replay Bias"""
        with self._lock:
            if not self.children:
                return None

            choices_weights = []
            for child in self.children:
                if child.visits > 0:
                    # Base UCB1
                    exploitation = child.value / child.visits
                    exploration = exploration_weight * math.sqrt(math.log(self.visits) / child.visits)

                    # Experience Replay Bias (if available)
                    # Note: Since this is a sync call in MCTS, we use a cached bias or small lookahead
                    # Real-world would pre-calculate this during node expansion
                    bias = 0.0
                    if experience_replay:
                        # Using a simplified version for the inner loop
                        pass

                    choices_weights.append(exploitation + exploration + bias)
                else:
                    choices_weights.append(float('inf'))

            if not choices_weights:
                return None

            best_idx = choices_weights.index(max(choices_weights))
            return self.children[best_idx]

    def add_child(self, state: str, action: str) -> 'MCTSNode':
        """Add a child node - thread-safe with bounded resources"""
        with self._child_lock:  # Protect child list during modification
            # Acquire resource from pool before creating new node
            resource = None
            try:
                # Attempt to acquire a resource from the pool (non-blocking)
                loop = asyncio.get_event_loop()
                resource = loop.run_until_complete(self._resource_pool.acquire())
            except Exception:
                # If resource pool is exhausted, return None or handle appropriately
                # This implements the bounded resource constraint
                logger.warning("⚠️ MCTS Node resource pool exhausted, pruning tree")
                return None

            child = MCTSNode(state, parent=self, action=action)
            self.children.append(child)
            return child

    def remove_child(self, child_node: 'MCTSNode'):
        """Remove a child node - thread-safe"""
        with self._child_lock:
            if child_node in self.children:
                self.children.remove(child_node)
                # Release resource back to pool
                loop = asyncio.get_event_loop()
                loop.run_until_complete(self._resource_pool.release(child_node))

    def get_child_count(self) -> int:
        """Thread-safe way to get child count"""
        with self._child_lock:
            return len(self.children)

    def get_children(self) -> List['MCTSNode']:
        """Thread-safe way to get children"""
        with self._child_lock:
            return self.children.copy()

    def increment_visit(self):
        """Thread-safe visit count increment"""
        with self._lock:
            self.visits += 1

    def update_value(self, value: float):
        """Thread-safe value update"""
        with self._lock:
            self.value += value


class System2Thinking:
    """
    System 2 thinking for complex reasoning
    - Uses MCTS to explore solution space
    - Self-evaluates each path with Process Reward Model
    - Returns best path after N iterations
    - Concurrency-safe operations with bounded resources
    - Watchdog timer for resource monitoring
    """

    def __init__(self, groq_api_key: str = None, memory_controller: MemoryController = None):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.client = Groq(api_key=self.groq_api_key) if Groq and self.groq_api_key else None
        self.memory = memory_controller or MemoryController()

        self.model = "llama-3.3-70b-versatile"
        self.max_iterations = 10
        self.max_depth = 5

        # Add concurrency safety
        self._global_lock = RLock()

        # Resource management
        self._executor = ThreadPoolExecutor(max_workers=5)  # Limit concurrent operations

        # Add watchdog timer for monitoring resource usage
        self._watchdog = resilience_manager.get_watchdog("system2_thinking", timeout_seconds=300.0)  # 5 minute timeout

        # Bounded resource pool for tree operations
        self._mcts_pool = resilience_manager.get_resource_pool("mcts_operations", max_size=50)

        # Track resource usage
        self._active_threads = 0
        self._thread_lock = Lock()

        logger.info("🧠 System 2 Thinking initialized with concurrency safety and resource management")

    async def reason(
        self,
        problem: str,
        context: str = "",
        max_iterations: int = None,
        max_depth: int = None
    ) -> Dict[str, Any]:
        """
        Deep reasoning using MCTS + PRM with security validations
        Concurrency-safe with bounded resources and watchdog timer

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

        if not isinstance(problem, str) or not problem.strip():
            return {"solution": "", "reasoning_path": [], "confidence": 0.0, "time_ms": 0, "error": "invalid_problem"}

        problem = problem[:MAX_PROBLEM_CHARS]
        context = (context or "")[:MAX_CONTEXT_CHARS]

        if not input_validator.validate_input(problem, 'general', max_length=MAX_PROBLEM_CHARS):
            return {"solution": "", "reasoning_path": [], "confidence": 0.0, "time_ms": 0, "error": "invalid_problem_content"}
        if context and not input_validator.validate_input(context, 'general', max_length=MAX_CONTEXT_CHARS):
            return {"solution": "", "reasoning_path": [], "confidence": 0.0, "time_ms": 0, "error": "invalid_context_content"}

        start_time = time.time()
        max_iterations = max(1, min(max_iterations or self.max_iterations, MAX_MCTS_ITERATIONS))
        max_depth = max(1, min(max_depth or self.max_depth, MAX_MCTS_DEPTH))

        logger.info(f"🧠 Starting System 2 reasoning: {problem[:50]}...")

        # Acquire resource from pool before starting work
        resource_acquired = False
        try:
            resource = await self._mcts_pool.acquire()
            resource_acquired = True

            # Start watchdog timer to monitor execution
            await self._watchdog.start()

            # Initialize MCTS root with security validation
            initial_state = f"Problem: {problem}\nContext: {context}\n\nLet me think step by step:"[:MAX_STATE_CHARS]

            # Validate that the initial state is safe before creating the node
            if not input_validator.validate_input(initial_state, 'reasoning_state', max_length=MAX_STATE_CHARS):
                logger.error("❌ Initial reasoning state validation failed")
                return {"solution": "", "reasoning_path": [], "confidence": 0.0, "time_ms": 0, "error": "unsafe_initial_state"}

            root = MCTSNode(state=initial_state)

            # Generate initial possible actions with security check
            root.untried_actions = self._generate_actions(initial_state, problem)

            # Validate the number of possible actions to prevent excessive exploration
            if len(root.untried_actions) > 20:  # Arbitrary limit to prevent explosion
                root.untried_actions = root.untried_actions[:20]
                logger.warning("⚠️ Limiting number of possible actions to prevent excessive exploration")

            # MCTS iterations with concurrency safety
            best_node = root
            best_value = -float('inf')

            for iteration in range(max_iterations):
                logger.info(f"🔄 MCTS iteration {iteration + 1}/{max_iterations}")

                # Reset watchdog for each iteration to prevent timeout
                await self._watchdog.reset()

                # Selection - check if we should continue based on security state
                node = await self._select_async(root)

                # Expansion with resource monitoring
                if not node.is_fully_expanded() and node.visits > 0:
                    node = await self._expand_async(node, problem)

                # Simulation - validate the node state before simulation
                if not input_validator.validate_input(node.state, 'reasoning_state', max_length=MAX_STATE_CHARS):
                    logger.warning("⚠️ Unsafe state detected during simulation, skipping")
                    continue

                value = await self._simulate_async(node, problem, max_depth)

                # Validate the value before backpropagation
                if not isinstance(value, (int, float)) or value < -100 or value > 100:
                    logger.warning(f"⚠️ Invalid value {value} from simulation, skipping backpropagation")
                    continue

                # Backpropagation with resource monitoring
                await self._backpropagate_async(node, value)

                # Track best node - validate before tracking
                if value > best_value:
                    if isinstance(value, (int, float)) and -100 <= value <= 100:
                        best_value = value
                        best_node = node

                # Check if we're approaching resource limits
                pool_stats = self._mcts_pool.get_stats()
                if pool_stats['checked_out'] > pool_stats['max_size'] * 0.9:  # 90% utilization
                    logger.warning(f"⚠️ MCTS resource pool at {pool_stats['utilization']*100:.1f}% capacity")

            # Extract best reasoning path
            reasoning_path = await self._extract_path_async(best_node)
            solution = reasoning_path[-1] if reasoning_path else ""

            elapsed_ms = int((time.time() - start_time) * 1000)

            logger.info(f"✅ System 2 reasoning complete in {elapsed_ms}ms (confidence: {best_value:.2f})")

            # Update health indicator for resource usage
            resilience_manager.update_health_indicator("system2_resource_utilization",
                                                     pool_stats['checked_out'],
                                                     pool_stats['max_size'])

            return {
                "solution": solution,
                "reasoning_path": reasoning_path,
                "confidence": best_value,
                "time_ms": elapsed_ms,
                "iterations": max_iterations,
                "resource_utilization": pool_stats['utilization']
            }

        except asyncio.TimeoutError:
            logger.error("❌ System 2 reasoning timed out by watchdog timer")
            return {"solution": "", "reasoning_path": [], "confidence": 0.0, "time_ms": int((time.time() - start_time) * 1000), "error": "timeout"}
        except Exception as e:
            logger.error(f"❌ System 2 reasoning failed: {e}")
            return {"solution": "", "reasoning_path": [], "confidence": 0.0, "time_ms": int((time.time() - start_time) * 1000), "error": "execution_failed"}
        finally:
            # Always stop the watchdog and release resources
            if resource_acquired:
                await self._mcts_pool.release(resource)
            await self._watchdog.stop()

    async def _select_async(self, node: MCTSNode) -> MCTSNode:
        """Select a node to expand using UCB1 - async with concurrency safety"""
        current_node = node
        while current_node.get_child_count() > 0:  # Thread-safe access
            if not current_node.is_fully_expanded():
                return current_node

            # Best child selection with thread safety
            best_child = current_node.best_child()
            if best_child is None:
                break
            current_node = best_child

        return current_node

    async def _expand_async(self, node: MCTSNode, problem: str) -> MCTSNode:
        """Expand node by trying an untried action - async with resource management"""
        # Thread-safe check for untried actions
        with node._lock:
            if not node.untried_actions:
                return node

            action = node.untried_actions.pop()

        new_state = await self._apply_action_async(node.state, action, problem)

        # Add child with bounded resource allocation
        child = node.add_child(new_state, action)
        if child is None:  # Resource pool was exhausted
            logger.warning("⚠️ Unable to expand node - resource pool exhausted")
            return node

        # Generate actions for child
        child.untried_actions = self._generate_actions(new_state, problem)

        return child

    async def _simulate_async(self, node: MCTSNode, problem: str, max_depth: int) -> float:
        """Simulate reasoning from node and evaluate with PRM - async with resource limits"""
        current_state = node.state
        depth = 0

        # Simulate reasoning steps with resource monitoring
        while depth < max_depth:
            # Check resource usage periodically
            if depth % 2 == 0:  # Check every 2 steps
                await self._watchdog.reset()  # Reset watchdog timer

                # Check if we're approaching resource limits
                pool_stats = self._mcts_pool.get_stats()
                if pool_stats['checked_out'] > pool_stats['max_size'] * 0.95:  # 95% utilization
                    logger.warning("⚠️ Approaching resource limits in simulation, stopping early")
                    break

            # Generate next reasoning step
            # PhD Synapse: Query memory before generating step
            memories = self.memory.retrieve(current_state[:500], top_k=2)
            if memories:
                current_state += f"\n[Historical Context: {memories[0]['text'][:200]}]"

            next_step = await self._generate_reasoning_step_async(current_state, problem)
            if not next_step or "FINAL ANSWER:" in next_step:
                break

            current_state += f"\n{next_step}"
            if len(current_state) > MAX_STATE_CHARS:
                current_state = current_state[-MAX_STATE_CHARS:]
            depth += 1

        # Evaluate with Process Reward Model
        value = await self._evaluate_reasoning_async(current_state, problem)

        return value

    async def _backpropagate_async(self, node: MCTSNode, value: float):
        """Backpropagate value up the tree - async with concurrency safety"""
        current_node = node
        while current_node:
            # Concurrency-safe update of visits and value
            current_node.increment_visit()
            current_node.update_value(value)

            # Move to parent
            current_node = current_node.parent

            # Reset watchdog periodically during backpropagation
            if current_node is not None and current_node.visits % 10 == 0:
                await self._watchdog.reset()

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

    async def _apply_action_async(self, state: str, action: str, problem: str) -> str:
        """Apply reasoning action to generate new state - async with resilience"""
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

    async def _generate_reasoning_step_async(self, state: str, problem: str) -> str:
        """Generate next reasoning step - async with resource monitoring"""
        try:
            # Check resource usage before making API call
            await self._watchdog.reset()

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

    async def _evaluate_reasoning_async(self, reasoning: str, problem: str) -> float:
        """
        Process Reward Model: Evaluate quality of reasoning
        Returns: Score between 0.0 and 1.0
        Async with resource monitoring
        """
        try:
            safe_problem = problem[:MAX_PROBLEM_CHARS]
            safe_reasoning = reasoning[:MAX_EVAL_CHARS]
            if not input_validator.validate_input(safe_problem, 'general', max_length=MAX_PROBLEM_CHARS):
                return 0.0
            if not input_validator.validate_input(safe_reasoning, 'general', max_length=MAX_EVAL_CHARS):
                return 0.0

            prompt = f"""Evaluate the quality of this reasoning for solving the problem.
Score from 0.0 (poor) to 1.0 (excellent).

Problem: {safe_problem}

Reasoning:
{safe_reasoning}

Evaluation criteria:
- Logical consistency
- Completeness
- Correctness
- Clarity

Return only a number between 0.0 and 1.0."""

            # Reset watchdog before making evaluation call
            await self._watchdog.reset()

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
            logger.debug(f"PRM raw response: '{score_text}'")

            # Robust score extraction with multiple parsing strategies
            score = self._extract_score_robust(score_text)

            return score

        except Exception as e:
            logger.error(f"❌ Evaluation failed: {e}")
            return 0.5  # Default neutral score

    def _extract_score_robust(self, score_text: str) -> float:
        """
        Robustly extract numeric score from LLM response with multiple fallback strategies
        """
        if not score_text:
            logger.warning("⚠️ Empty score response received")
            return 0.5

        # Strategy 1: Look for JSON-like patterns
        import re
        import json

        # Try to find JSON objects
        json_pattern = r'\{[^}]*"?(score|value|result)"?[^}]*:[^}]*\}'
        json_match = re.search(json_pattern, score_text, re.IGNORECASE)
        if json_match:
            try:
                json_str = json_match.group(0)
                # Clean up the JSON string
                json_str = re.sub(r'([^"\\])"', r'\1"', json_str)  # Fix quotes
                json_str = re.sub(r':\s*"', r': "', json_str)     # Fix colons

                # Try to parse as JSON
                data = json.loads(json_str)
                for key in ['score', 'value', 'result']:
                    if key in data:
                        score = float(data[key])
                        return max(0.0, min(1.0, score))
            except (json.JSONDecodeError, ValueError) as e:
                logger.debug(f"JSON parsing failed: {e}")

        # Strategy 2: Look for numeric patterns with context
        # Pattern: "score: 0.85" or "Score is 0.75" or "0.9"
        numeric_patterns = [
            r'(?:score|value|result|rating)[\s:]*([0-9]+\.?[0-9]*)',  # score: 0.85
            r'([0-9]+\.?[0-9]*)\s*(?:is the score|score is)',        # 0.85 is the score
        ]

        for pattern in numeric_patterns:
            matches = re.findall(pattern, score_text, re.IGNORECASE)
            logger.debug(f"🔍 Pattern '{pattern}' for '{score_text}' -> matches: {matches}")

            for match in matches:
                try:
                    # Handle case where match is a tuple (from groups)
                    if isinstance(match, tuple):
                        match = match[0] if match[0] else match[1]

                    score = float(match)
                    if 0.0 <= score <= 1.0:
                        logger.debug(f"✅ Parsed score using pattern '{pattern}': {score}")
                        return score
                except ValueError:
                    continue

        # Strategy 3: Look for percentage patterns and convert
        percentage_match = re.search(r'([0-9]{1,3})%', score_text)
        logger.debug(f"🔍 Checking percentage pattern for: '{score_text}' -> match: {percentage_match}")
        if percentage_match:
            try:
                percentage = float(percentage_match.group(1))
                score = percentage / 100.0
                logger.debug(f"✅ Parsed percentage score: {percentage}% -> {score}")
                return max(0.0, min(1.0, score))
            except ValueError:
                pass

        # Also look for "percent" text
        percent_match = re.search(r'([0-9]{1,3})\s*percent', score_text, re.IGNORECASE)
        logger.debug(f"🔍 Checking percent pattern for: '{score_text}' -> match: {percent_match}")
        if percent_match:
            try:
                percentage = float(percent_match.group(1))
                score = percentage / 100.0
                logger.debug(f"✅ Parsed percentage score (percent): {percentage}% -> {score}")
                return max(0.0, min(1.0, score))
            except ValueError:
                pass

        # Strategy 4: Look for "out of" patterns before generic numeric patterns
        out_of_match = re.search(r'([0-9]+)\s+out of\s+([0-9]+)', score_text, re.IGNORECASE)
        logger.debug(f"🔍 Checking 'out of' pattern for: '{score_text}' -> match: {out_of_match}")
        if out_of_match:
            try:
                numerator = float(out_of_match.group(1))
                denominator = float(out_of_match.group(2))
                score = numerator / denominator
                logger.debug(f"✅ Parsed 'out of' score: {numerator}/{denominator} -> {score}")
                return max(0.0, min(1.0, score))
            except (ValueError, ZeroDivisionError):
                pass

        # Strategy 4: Look for fraction patterns
        fraction_match = re.search(r'([0-9]+)\s*/\s*([0-9]+)', score_text)
        logger.debug(f"🔍 Checking fraction pattern for: '{score_text}' -> match: {fraction_match}")
        if fraction_match:
            try:
                numerator = float(fraction_match.group(1))
                denominator = float(fraction_match.group(2))
                score = numerator / denominator
                logger.debug(f"✅ Parsed fraction score: {numerator}/{denominator} -> {score}")
                return max(0.0, min(1.0, score))
            except (ValueError, ZeroDivisionError):
                pass

        # Also look for "out of" patterns
        out_of_match = re.search(r'([0-9]+)\s+out of\s+([0-9]+)', score_text, re.IGNORECASE)
        logger.debug(f"🔍 Checking 'out of' pattern for: '{score_text}' -> match: {out_of_match}")
        if out_of_match:
            try:
                numerator = float(out_of_match.group(1))
                denominator = float(out_of_match.group(2))
                score = numerator / denominator
                logger.debug(f"✅ Parsed 'out of' score: {numerator}/{denominator} -> {score}")
                return max(0.0, min(1.0, score))
            except (ValueError, ZeroDivisionError):
                pass

        # Strategy 5: Look for word-based scores
        word_scores = {
            'excellent': 1.0, 'perfect': 1.0, 'outstanding': 0.95,
            'very good': 0.9, 'good': 0.8, 'satisfactory': 0.7,
            'average': 0.6, 'fair': 0.5, 'poor': 0.3,
            'bad': 0.2, 'terrible': 0.1, 'awful': 0.05
        }

        score_text_lower = score_text.lower()
        for word, score in word_scores.items():
            if word in score_text_lower:
                logger.debug(f"✅ Parsed word-based score: '{word}' -> {score}")
                return score

        # Strategy 6: Last resort - try to find any number and normalize
        all_numbers = re.findall(r'[0-9]+\.?[0-9]*', score_text)
        if not all_numbers:
            return 0.5

        # Try to find the most relevant number
        # Strategy: Look for numbers that are likely the actual score
        # Priority: 1) Numbers between 1-100 that are NOT 0, 100 (likely scores)
        #          2) Numbers between 0-1 (decimal scores)
        #          3) Last number found (most recent in text)

        # First pass: look for scores between 1-99 (most likely the actual score)
        for num_str in all_numbers:
            try:
                num = float(num_str)
                if 1 <= num <= 99:  # Likely a score out of 100
                    score = num / 100.0
                    logger.debug(f"✅ Parsed score between 1-99: {num} -> {score}")
                    return score
            except ValueError:
                continue

        # Second pass: look for decimal scores between 0-1
        for num_str in all_numbers:
            try:
                num = float(num_str)
                if 0 <= num <= 1.0 and '.' in num_str:
                    logger.debug(f"✅ Parsed decimal score: {num}")
                    return num
            except ValueError:
                continue

        # Third pass: look for other numbers between 0-100
        for num_str in all_numbers:
            try:
                num = float(num_str)
                if 0 <= num <= 100:
                    if num == 0 or num == 100:
                        # Skip obvious boundary values that are likely not the score
                        continue
                    if '.' in num_str or num <= 1.0:
                        # Likely a decimal score
                        if 0 <= num <= 1.0:
                            logger.debug(f"✅ Parsed decimal score: {num}")
                            return num
                    else:
                        # Likely a percentage
                        score = num / 100.0
                        logger.debug(f"✅ Parsed percentage score (fallback): {num}% -> {score}")
                        return score
            except ValueError:
                continue

        # Final fallback - use the last number found (most recent in the text)
        if all_numbers:
            try:
                last_num_str = all_numbers[-1]
                last_num = float(last_num_str)
                if 0 <= last_num <= 100:
                    if last_num <= 1.0:
                        logger.debug(f"✅ Parsed last number as decimal score: {last_num}")
                        return last_num
                    else:
                        score = last_num / 100.0
                        logger.debug(f"✅ Parsed last number as percentage score: {last_num}% -> {score}")
                        return score
            except ValueError:
                pass

        # Final fallback
        logger.warning(f"⚠️ Could not parse score from: '{score_text}'")
        logger.warning("   Available strategies: JSON, numeric patterns, percentages, fractions, word scores")
        logger.warning("   Consider improving the Prompt Reward Model prompt for better parsing")
        return 0.5  # Default neutral score

    async def _extract_path_async(self, node: MCTSNode) -> List[str]:
        """Extract reasoning path from root to node - async with concurrency safety"""
        path = []
        current = node

        while current:
            # Thread-safe access to action
            with current._lock:
                if current.action:
                    path.append(f"{current.action}: {current.state.split(current.action)[-1].strip()[:200]}")

            # Move to parent with safety
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

# ==========================================================
# JARVIS v9.0 - Skill Graph
# Builds knowledge graph of skills with dependencies,
# preconditions, effects, and composability
# ==========================================================

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, field, asdict
from collections import defaultdict
import networkx as nx

logger = logging.getLogger(__name__)


@dataclass
class SkillNode:
    """Represents a skill in the graph"""
    name: str
    description: str
    path: str
    tags: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)

    # Skill graph - what this skill needs and produces
    preconditions: List[str] = field(default_factory=list)  # Required inputs
    effects: List[str] = field(default_factory=list)  # Produced outputs
    dependencies: List[str] = field(default_factory=list)  # Other skills this needs

    # Type signature for composition
    input_type: str = "any"
    output_type: str = "any"

    # Metadata
    risk_level: str = "unknown"
    source: str = "community"
    date_added: str = ""

    # Graph metrics
    in_degree: int = 0
    out_degree: int = 0
    centrality: float = 0.0

    def to_dict(self) -> Dict:
        return asdict(self)


class SkillGraph:
    """
    Knowledge graph of skills with:
    - Dependency tracking
    - Composition validation
    - Workflow synthesis support
    """

    def __init__(self, skills_path: str = None):
        if skills_path is None:
            skills_path = os.getenv("SKILLS_PATH", "./skills")

        self.skills_path = Path(skills_path)
        self.graph = nx.DiGraph()  # Directed graph for dependencies
        self.skills: Dict[str, SkillNode] = {}
        self.skill_chains: Dict[str, List[str]] = {}  # Cached chains

        # Type ontology for composition validation
        self.type_ontology = {
            "analysis": ["security_analysis", "performance_analysis", "code_analysis"],
            "output": ["report", "summary", "recommendations", "code"],
            "action": ["test", "deploy", "fix", "optimize", "refactor"],
            "input": ["code", "api_spec", "config", "logs", "metrics"],
        }

        # Common skill patterns
        self.skill_patterns = {
            "audit": {"preconditions": ["system", "access"], "effects": ["report", "findings"]},
            "test": {"preconditions": ["code", "spec"], "effects": ["results", "coverage"]},
            "optimize": {"preconditions": ["system", "metrics"], "effects": ["optimized_system", "benchmarks"]},
            "fix": {"preconditions": ["bug", "code"], "effects": ["fixed_code", "tests"]},
            "generate": {"preconditions": ["spec", "requirements"], "effects": ["code", "docs"]},
            "analyze": {"preconditions": ["data", "context"], "effects": ["insights", "report"]},
            "deploy": {"preconditions": ["build", "config"], "effects": ["deployment", "logs"]},
        }

        self.build_graph()
        logger.info(f"🕷️ Skill Graph built with {len(self.skills)} nodes")

    def build_graph(self):
        """Build skill graph from skill files"""
        if not self.skills_path.exists():
            logger.warning(f"Skills path not found: {self.skills_path}")
            return

        for skill_dir in self.skills_path.iterdir():
            if skill_dir.is_dir():
                skill_md = skill_dir / "SKILL.md"
                if skill_md.exists():
                    skill_node = self._parse_skill(skill_md, skill_dir)
                    if skill_node:
                        self.skills[skill_node.name] = skill_node
                        self.graph.add_node(skill_node.name, **skill_node.to_dict())

        # Build dependency edges
        self._build_dependency_edges()

        # Calculate graph metrics
        self._calculate_metrics()

    def _parse_skill(self, skill_md_path: Path, skill_dir: Path) -> Optional[SkillNode]:
        """Parse skill file with enhanced extraction"""
        try:
            content = skill_md_path.read_text(encoding='utf-8')

            # Extract YAML frontmatter
            metadata = {}
            if content.startswith('---'):
                parts = content.split('---', 2)
                if len(parts) >= 3:
                    yaml_content = parts[1]
                    for line in yaml_content.strip().split('\n'):
                        if ':' in line and not line.startswith(' ') and not line.startswith('-'):
                            key, value = line.split(':', 1)
                            metadata[key.strip()] = value.strip()
                        elif metadata:
                            last_key = list(metadata.keys())[-1]
                            metadata[last_key] = metadata[last_key] + ' ' + line.strip()

            # Extract inferred preconditions/effects from content
            preconditions = self._extract_preconditions(content)
            effects = self._extract_effects(content)
            dependencies = self._extract_dependencies(content)

            # Infer type signature from skill name
            input_type, output_type = self._infer_type_signature(metadata.get('name', ''))

            return SkillNode(
                name=metadata.get('name', '').strip(),
                description=metadata.get('description', ''),
                path=str(skill_dir),
                tags=[t.strip() for t in metadata.get('tags', '').split(',') if t.strip()],
                tools=[t.strip() for t in metadata.get('tools', '').split(',') if t.strip()],
                preconditions=preconditions,
                effects=effects,
                dependencies=dependencies,
                input_type=input_type,
                output_type=output_type,
                risk_level=metadata.get('risk', 'unknown'),
                source=metadata.get('source', 'community'),
                date_added=metadata.get('date_added', '')
            )
        except Exception as e:
            logger.debug(f"Failed to parse skill {skill_md_path}: {e}")
            return None

    def _extract_preconditions(self, content: str) -> List[str]:
        """Extract preconditions from skill content"""
        preconditions = []

        # Look for "when" sections
        if "when" in content.lower():
            when_section = content.lower().split("when")[1].split("do not")[0]
            if "improving" in when_section: preconditions.append("existing_system")
            if "analyzing" in when_section: preconditions.append("data")
            if "testing" in when_section: preconditions.append("code")

        # Look for required inputs
        input_patterns = {
            "requires": [],
            "needs": [],
            "input": [],
            "given": [],
        }

        for pattern, matches in input_patterns.items():
            if pattern in content.lower():
                # Extract nouns after pattern
                pass

        # Infer from skill name
        content_lower = content.lower()
        if "audit" in content_lower: preconditions.extend(["system", "access"])
        if "test" in content_lower: preconditions.extend(["code", "spec"])
        if "optimize" in content_lower: preconditions.extend(["system", "metrics"])
        if "security" in content_lower: preconditions.append("system")
        if "performance" in content_lower: preconditions.extend(["system", "metrics"])
        if "api" in content_lower: preconditions.append("api_spec")

        return list(set(preconditions))

    def _extract_effects(self, content: str) -> List[str]:
        """Extract effects/outcomes from skill content"""
        effects = []

        # Look for success criteria
        if "success" in content.lower():
            success_section = content.lower().split("success")[1].split("##")[0]
            if "improves" in success_section: effects.append("improved_system")
            if "report" in success_section: effects.append("report")

        # Infer from skill category
        content_lower = content.lower()
        if "audit" in content_lower: effects.extend(["report", "findings"])
        if "test" in content_lower: effects.extend(["results", "coverage"])
        if "optimize" in content_lower: effects.extend(["optimized_system", "benchmarks"])
        if "fix" in content_lower: effects.extend(["fixed_code", "tests"])
        if "generate" in content_lower: effects.extend(["code", "docs"])
        if "analyze" in content_lower: effects.extend(["insights", "report"])
        if "security" in content_lower: effects.extend(["security_report", "recommendations"])

        return list(set(effects))

    def _extract_dependencies(self, content: str) -> List[str]:
        """Extract skill dependencies from content"""
        dependencies = []

        # Look for "Use:" commands
        import re
        uses = re.findall(r'Use:\s*([\w-]+)', content)
        dependencies.extend(uses)

        # Look for tool dependencies
        if "context-manager" in content.lower(): dependencies.append("context-manager")
        if "prompt-engineer" in content.lower(): dependencies.append("prompt-engineer")
        if "parallel-test" in content.lower(): dependencies.append("parallel-test-runner")

        return list(set(dependencies))

    def _infer_type_signature(self, skill_name: str) -> Tuple[str, str]:
        """Infer input/output types from skill name"""
        name_lower = skill_name.lower()

        # Input type inference
        if "api" in name_lower: input_type = "api_spec"
        elif "code" in name_lower: input_type = "code"
        elif "performance" in name_lower: input_type = "metrics"
        elif "security" in name_lower: input_type = "system"
        elif "test" in name_lower: input_type = "code"
        elif "audit" in name_lower: input_type = "system"
        elif "optimize" in name_lower: input_type = "system"
        elif "fix" in name_lower: input_type = "bug"
        else: input_type = "any"

        # Output type inference
        if "audit" in name_lower: output_type = "report"
        elif "test" in name_lower: output_type = "results"
        elif "optimize" in name_lower: output_type = "optimized_system"
        elif "fix" in name_lower: output_type = "fixed_code"
        elif "generate" in name_lower: output_type = "code"
        elif "analyze" in name_lower: output_type = "insights"
        elif "security" in name_lower: output_type = "security_report"
        elif "recommend" in name_lower: output_type = "recommendations"
        else: output_type = "any"

        return input_type, output_type

    def _build_dependency_edges(self):
        """Build edges between skills based on dependencies"""
        for skill_name, skill_node in self.skills.items():
            for dep in skill_node.dependencies:
                if dep in self.skills:
                    self.graph.add_edge(dep, skill_name)

            # Add composition edges based on type compatibility
            for other_name, other_node in self.skills.items():
                if other_name == skill_name:
                    continue

                # If other's output matches this's input, add edge
                if self._types_compatible(other_node.output_type, skill_node.input_type):
                    self.graph.add_edge(other_name, skill_name, type="composition")

    def _types_compatible(self, output_type: str, input_type: str) -> bool:
        """Check if output type can satisfy input type"""
        if input_type == "any" or output_type == "any":
            return True

        # Direct match
        if output_type == input_type:
            return True

        # Ontology match
        for category, types in self.type_ontology.items():
            if output_type in types and input_type in types:
                return True

        # Specialization
        if input_type == "system" and output_type in ["api_spec", "code", "metrics"]:
            return True

        return False

    def _calculate_metrics(self):
        """Calculate graph metrics for each node"""
        for skill_name in self.graph.nodes():
            self.graph.nodes[skill_name]["in_degree"] = self.graph.in_degree(skill_name)
            self.graph.nodes[skill_name]["out_degree"] = self.graph.out_degree(skill_name)

        # Calculate centrality
        try:
            centrality = nx.degree_centrality(self.graph)
            for skill_name, score in centrality.items():
                self.skills[skill_name].centrality = score
                self.graph.nodes[skill_name]["centrality"] = score
        except:
            pass

    def find_skill_chain(self, goal: str, max_length: int = 5) -> List[str]:
        """Find a chain of skills that achieves the goal"""
        # Match skills to goal
        matched = self._match_goal(goal)

        if not matched:
            return []

        # Start from end goal and work backwards
        end_skill = matched[0]

        # Find prerequisite chain
        chain = [end_skill]
        current = end_skill

        while len(chain) < max_length:
            predecessors = list(self.graph.predecessors(current))
            if not predecessors:
                break

            # Pick highest centrality predecessor
            best = max(predecessors, key=lambda x: self.skills[x].centrality if x in self.skills else 0)
            chain.insert(0, best)
            current = best

        self.skill_chains[goal] = chain
        return chain

    def _match_goal(self, goal: str) -> List[str]:
        """Match skills to a goal description"""
        matches = []
        goal_lower = goal.lower()

        for skill_name, skill_node in self.skills.items():
            score = 0

            # Name match
            if skill_name.lower() in goal_lower or goal_lower in skill_name.lower():
                score += 10

            # Description match
            if goal_lower in skill_node.description.lower():
                score += 5

            # Tag match
            for tag in skill_node.tags:
                if tag.lower() in goal_lower:
                    score += 3

            # Effect match (skill produces what goal needs)
            for effect in skill_node.effects:
                if effect in goal_lower:
                    score += 5

            if score > 0:
                matches.append((skill_name, score))

        matches.sort(key=lambda x: x[1], reverse=True)
        return [m[0] for m in matches[:10]]

    def validate_composition(self, skill_chain: List[str]) -> Tuple[bool, str]:
        """Validate that skills can be composed in order"""
        if len(skill_chain) < 2:
            return True, "Single skill - no composition needed"

        for i in range(len(skill_chain) - 1):
            current = self.skills.get(skill_chain[i])
            next_skill = self.skills.get(skill_chain[i + 1])

            if not current or not next_skill:
                return False, f"Unknown skill in chain"

            # Check type compatibility
            if not self._types_compatible(current.output_type, next_skill.input_type):
                return False, f"Type mismatch: {current.output_type} → {next_skill.input_type}"

            # Check if edge exists
            if not self.graph.has_edge(skill_chain[i], skill_chain[i + 1]):
                # Check if there's any path
                if not nx.has_path(self.graph, skill_chain[i], skill_chain[i + 1]):
                    return False, f"No path between {skill_chain[i]} and {skill_chain[i + 1]}"

        return True, "Composition valid"

    def get_parallel_groups(self, skill_chain: List[str]) -> List[List[str]]:
        """Group skills that can run in parallel"""
        # Skills with no dependencies between them can run in parallel
        groups = []
        remaining = set(skill_chain)

        while remaining:
            # Find skills with all predecessors already scheduled
            ready = []
            for skill in remaining:
                predecessors = set(self.graph.predecessors(skill))
                if not predecessors.intersection(remaining):
                    ready.append(skill)

            if ready:
                groups.append(ready)
                remaining -= set(ready)
            else:
                # No progress - add remaining one by one
                groups.append([list(remaining)[0]])
                remaining = remaining - {list(remaining)[0]}

        return groups

    def get_skill_info(self, skill_name: str) -> Optional[Dict]:
        """Get detailed skill information"""
        if skill_name not in self.skills:
            return None

        node = self.skills[skill_name]
        return {
            "name": node.name,
            "description": node.description,
            "preconditions": node.preconditions,
            "effects": node.effects,
            "dependencies": node.dependencies,
            "input_type": node.input_type,
            "output_type": node.output_type,
            "tags": node.tags,
            "tools": node.tools,
            "centrality": node.centrality,
            "in_degree": node.in_degree,
            "out_degree": node.out_degree
        }

    def get_stats(self) -> Dict:
        """Get graph statistics"""
        return {
            "total_skills": len(self.skills),
            "total_edges": self.graph.number_of_edges(),
            "avg_degree": sum(self.graph.degree(n) for n in self.graph.nodes()) / max(len(self.skills), 1),
            "density": nx.density(self.graph),
            "connected_components": nx.number_weakly_connected_components(self.graph) if self.graph.number_of_nodes() > 0 else 0
        }

    def visualize_ascii(self, max_nodes: int = 20) -> str:
        """Generate ASCII visualization of skill graph"""
        # Get top nodes by centrality
        top_nodes = sorted(self.skills.keys(), key=lambda x: self.skills[x].centrality, reverse=True)[:max_nodes]

        output = "=" * 60 + "\n"
        output += "SKILL GRAPH (Top {} nodes by centrality)\n".format(max_nodes)
        output += "=" * 60 + "\n\n"

        for node in top_nodes:
            skill = self.skills[node]
            connections = list(self.graph.successors(node))
            output += f"{node}\n"
            output += f"  ├─ in: {skill.in_degree}, out: {skill.out_degree}, centrality: {skill.centrality:.3f}\n"
            if connections:
                output += f"  └─ → {', '.join(connections[:5])}{'...' if len(connections) > 5 else ''}\n"
            output += "\n"

        return output

    def save(self, filepath: str):
        """Save graph state"""
        data = {
            "skills": {k: v.to_dict() for k, v in self.skills.items()},
            "edges": list(self.graph.edges()),
            "stats": self.get_stats()
        }
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)
        logger.info(f"💾 Skill graph saved to {filepath}")


# Test
if __name__ == "__main__":
    graph = SkillGraph()

    print("\n" + "=" * 60)
    print("SKILL GRAPH STATS")
    print("=" * 60)
    print(json.dumps(graph.get_stats(), indent=2))

    print("\n" + "=" * 60)
    print("SKILL CHAIN EXAMPLE")
    print("=" * 60)
    chain = graph.find_skill_chain("security audit")
    print(f"Goal: 'security audit'")
    print(f"Chain: {' → '.join(chain)}")
    valid, msg = graph.validate_composition(chain)
    print(f"Valid: {valid} - {msg}")

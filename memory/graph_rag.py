# ==========================================================
# JARVIS v9.0 - GraphRAG Implementation
# Microsoft GraphRAG: Entity extraction, knowledge graph, community detection
# Answers global questions like "What are the themes of my projects?"
# ==========================================================

import networkx as nx
import json
import logging
from typing import List, Dict, Any, Tuple, Set
from collections import defaultdict
import re
from datetime import datetime

try:
    from groq import Groq
except ImportError:
    Groq = None

logger = logging.getLogger(__name__)


class GraphRAG:
    """
    GraphRAG implementation for JARVIS v9.0
    - Extracts entities and relationships from conversations
    - Builds knowledge graph
    - Performs community detection
    - Answers global queries
    """

    def __init__(self, groq_api_key: str = None):
        self.graph = nx.DiGraph()
        self.communities = {}
        self.entity_cache = {}
        self.groq_client = Groq(api_key=groq_api_key) if Groq and groq_api_key else None
        logger.info("🕸️ GraphRAG initialized")

    def extract_entities_and_relationships(self, text: str) -> Dict[str, Any]:
        """
        Extract entities and relationships from text using LLM
        Returns: {entities: [...], relationships: [...]}
        """
        if not self.groq_client:
            # Fallback: Simple regex-based extraction
            return self._extract_entities_regex(text)

        try:
            prompt = f"""Extract entities and relationships from this text.
Return JSON format:
{{
  "entities": [
    {{"name": "entity_name", "type": "person|project|concept|tool", "description": "brief description"}}
  ],
  "relationships": [
    {{"source": "entity1", "target": "entity2", "type": "works_on|uses|related_to", "description": "brief"}}
  ]
}}

Text: {text[:1000]}"""

            response = self.groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            logger.error(f"❌ Entity extraction failed: {e}")
            return self._extract_entities_regex(text)

    def _extract_entities_regex(self, text: str) -> Dict[str, Any]:
        """Fallback regex-based entity extraction"""
        entities = []
        relationships = []

        # Extract capitalized words as potential entities
        words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', text)
        for word in set(words):
            if len(word) > 2:
                entities.append({
                    "name": word,
                    "type": "concept",
                    "description": f"Mentioned in context"
                })

        return {"entities": entities, "relationships": relationships}

    def add_to_graph(self, text: str, metadata: Dict = None):
        """
        Add text to knowledge graph
        - Extracts entities and relationships
        - Updates graph structure
        """
        logger.info(f"📊 Adding to graph: {text[:50]}...")

        # Extract entities and relationships
        extracted = self.extract_entities_and_relationships(text)

        # Add entities as nodes
        for entity in extracted.get("entities", []):
            name = entity["name"]
            if name not in self.graph:
                self.graph.add_node(
                    name,
                    type=entity.get("type", "unknown"),
                    description=entity.get("description", ""),
                    first_seen=datetime.now().isoformat(),
                    mentions=1
                )
            else:
                # Increment mention count
                self.graph.nodes[name]["mentions"] = self.graph.nodes[name].get("mentions", 0) + 1

        # Add relationships as edges
        for rel in extracted.get("relationships", []):
            source = rel["source"]
            target = rel["target"]
            rel_type = rel.get("type", "related_to")

            if source in self.graph and target in self.graph:
                if self.graph.has_edge(source, target):
                    # Increment weight
                    self.graph[source][target]["weight"] += 1
                else:
                    self.graph.add_edge(
                        source,
                        target,
                        type=rel_type,
                        description=rel.get("description", ""),
                        weight=1
                    )

        # Update communities
        self._detect_communities()

        logger.info(f"✅ Graph updated: {self.graph.number_of_nodes()} nodes, {self.graph.number_of_edges()} edges")

    def _detect_communities(self):
        """Detect communities using Louvain algorithm"""
        if self.graph.number_of_nodes() < 3:
            return

        try:
            # Convert to undirected for community detection
            undirected = self.graph.to_undirected()

            # Use Louvain community detection
            import community as community_louvain
            self.communities = community_louvain.best_partition(undirected)

        except ImportError:
            # Fallback: Simple connected components
            undirected = self.graph.to_undirected()
            self.communities = {}
            for i, component in enumerate(nx.connected_components(undirected)):
                for node in component:
                    self.communities[node] = i

        logger.info(f"🔍 Detected {len(set(self.communities.values()))} communities")

    def query(self, question: str, top_k: int = 5) -> str:
        """
        Answer global questions using graph structure
        Examples:
        - "What are the themes of my projects?"
        - "How are X and Y related?"
        - "What tools do I use most?"
        """
        logger.info(f"🔍 GraphRAG query: {question}")

        if self.graph.number_of_nodes() == 0:
            return "No knowledge graph data available yet."

        # Analyze question type
        question_lower = question.lower()

        if "theme" in question_lower or "topic" in question_lower:
            return self._get_themes()

        elif "related" in question_lower or "connection" in question_lower:
            return self._get_relationships(question)

        elif "most" in question_lower or "frequently" in question_lower:
            return self._get_most_mentioned()

        else:
            # General query: return relevant entities
            return self._general_query(question)

    def _get_themes(self) -> str:
        """Get major themes from communities"""
        if not self.communities:
            return "No themes detected yet."

        # Group nodes by community
        community_groups = defaultdict(list)
        for node, comm_id in self.communities.items():
            community_groups[comm_id].append(node)

        # Build response
        themes = []
        for comm_id, nodes in sorted(community_groups.items(), key=lambda x: len(x[1]), reverse=True)[:5]:
            theme_name = f"Theme {comm_id + 1}"
            entities = ", ".join(nodes[:10])
            themes.append(f"**{theme_name}**: {entities}")

        return "Major themes in your knowledge graph:\n\n" + "\n".join(themes)

    def _get_relationships(self, question: str) -> str:
        """Find relationships between entities"""
        # Extract potential entity names from question
        words = re.findall(r'\b[A-Z][a-z]+\b', question)

        if len(words) < 2:
            return "Please specify two entities to find relationships."

        source, target = words[0], words[1]

        if source not in self.graph or target not in self.graph:
            return f"Entities '{source}' or '{target}' not found in graph."

        # Find shortest path
        try:
            path = nx.shortest_path(self.graph, source, target)
            path_str = " → ".join(path)
            return f"Relationship path: {path_str}"
        except nx.NetworkXNoPath:
            return f"No direct relationship found between {source} and {target}."

    def _get_most_mentioned(self) -> str:
        """Get most frequently mentioned entities"""
        if self.graph.number_of_nodes() == 0:
            return "No entities tracked yet."

        # Sort by mentions
        sorted_nodes = sorted(
            self.graph.nodes(data=True),
            key=lambda x: x[1].get("mentions", 0),
            reverse=True
        )[:10]

        result = "Most frequently mentioned:\n\n"
        for node, data in sorted_nodes:
            mentions = data.get("mentions", 0)
            node_type = data.get("type", "unknown")
            result += f"- **{node}** ({node_type}): {mentions} mentions\n"

        return result

    def _general_query(self, question: str) -> str:
        """General query: return relevant entities"""
        # Simple keyword matching
        question_lower = question.lower()
        relevant_nodes = []

        for node, data in self.graph.nodes(data=True):
            if node.lower() in question_lower or question_lower in node.lower():
                relevant_nodes.append((node, data))

        if not relevant_nodes:
            return "No relevant entities found for this query."

        result = "Relevant entities:\n\n"
        for node, data in relevant_nodes[:10]:
            node_type = data.get("type", "unknown")
            description = data.get("description", "")
            result += f"- **{node}** ({node_type}): {description}\n"

        return result

    def get_stats(self) -> Dict[str, Any]:
        """Get graph statistics"""
        return {
            "nodes": self.graph.number_of_nodes(),
            "edges": self.graph.number_of_edges(),
            "communities": len(set(self.communities.values())) if self.communities else 0,
            "density": nx.density(self.graph) if self.graph.number_of_nodes() > 0 else 0
        }

    def save(self, filepath: str):
        """Save graph to file"""
        data = {
            "nodes": [
                {"id": node, **data}
                for node, data in self.graph.nodes(data=True)
            ],
            "edges": [
                {"source": u, "target": v, **data}
                for u, v, data in self.graph.edges(data=True)
            ],
            "communities": self.communities
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"💾 Graph saved to {filepath}")

    def load(self, filepath: str):
        """Load graph from file"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self.graph.clear()

            # Add nodes
            for node_data in data.get("nodes", []):
                node_id = node_data.pop("id")
                self.graph.add_node(node_id, **node_data)

            # Add edges
            for edge_data in data.get("edges", []):
                source = edge_data.pop("source")
                target = edge_data.pop("target")
                self.graph.add_edge(source, target, **edge_data)

            self.communities = data.get("communities", {})

            logger.info(f"📂 Graph loaded from {filepath}")

        except Exception as e:
            logger.error(f"❌ Failed to load graph: {e}")


# Test
if __name__ == "__main__":
    import os

    graph = GraphRAG(groq_api_key=os.getenv("GROQ_API_KEY"))

    # Test data
    graph.add_to_graph("I'm working on JARVIS project using Python and FastAPI")
    graph.add_to_graph("JARVIS uses Groq API for LLM inference")
    graph.add_to_graph("I need to implement GraphRAG for better memory")

    print("\n" + "="*50)
    print("GRAPH STATS:", graph.get_stats())
    print("="*50)

    print("\n" + graph.query("What are the themes of my projects?"))
    print("\n" + graph.query("What tools do I use most?"))

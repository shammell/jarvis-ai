# ==========================================================
# JARVIS v9.0 - Memory Controller
# Integrates GraphRAG, ColBERT, and existing memory systems
# ==========================================================

import logging
from typing import List, Dict, Any, Optional
import os
import json
from datetime import datetime

logger = logging.getLogger(__name__)


class MemoryController:
    """
    Unified memory controller for JARVIS v9.0
    - GraphRAG for knowledge graph and global queries
    - ColBERT for precise retrieval
    - TF-IDF fallback for compatibility
    - SQLite for structured data
    - Redis for caching (optional)
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.storage_path = self.config.get("storage_path", "./memory_storage")
        os.makedirs(self.storage_path, exist_ok=True)

        # Initialize subsystems
        self._init_graph_rag()
        self._init_colbert()
        self._init_cache()

        logger.info("🧠 Memory Controller initialized")

    def _init_graph_rag(self):
        """Initialize GraphRAG"""
        try:
            from memory.graph_rag import GraphRAG

            groq_key = os.getenv("GROQ_API_KEY")
            self.graph_rag = GraphRAG(groq_api_key=groq_key)

            # Load existing graph if available
            graph_file = os.path.join(self.storage_path, "knowledge_graph.json")
            if os.path.exists(graph_file):
                self.graph_rag.load(graph_file)

            logger.info("✅ GraphRAG initialized")

        except Exception as e:
            logger.error(f"❌ GraphRAG initialization failed: {e}")
            self.graph_rag = None

    def _init_colbert(self):
        """Initialize ColBERT retriever"""
        try:
            from memory.colbert_retriever import ColBERTRetriever

            self.colbert = ColBERTRetriever()

            # Load existing documents if available
            colbert_file = os.path.join(self.storage_path, "colbert_docs.json")
            if os.path.exists(colbert_file):
                self.colbert.load(colbert_file)

            self._load_seed_documents()

            logger.info("✅ ColBERT initialized")

        except Exception as e:
            logger.error(f"❌ ColBERT initialization failed: {e}")
            self.colbert = None

    def _load_seed_documents(self):
        """Add seed documents if the retriever is empty."""
        if self.colbert and not self.colbert.documents:
            logger.info("🌱 No documents found in ColBERT. Loading seed documents.")
            seed_docs = [
                "JARVIS is a powerful AI assistant.",
                "The memory system uses ColBERT for advanced retrieval.",
                "System health and performance are continuously monitored.",
                "Antigravity skills provide extended capabilities.",
                "This is a seed document to prevent vocabulary errors."
            ]
            try:
                self.colbert.add_documents(seed_docs)
                logger.info(f"🌱 Loaded {len(seed_docs)} seed documents.")
            except Exception as e:
                logger.error(f"❌ Failed to load seed documents: {e}")

    def _init_cache(self):
        """Initialize Redis cache (optional)"""
        try:
            import redis
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))

            self.cache = redis.Redis(
                host=redis_host,
                port=redis_port,
                decode_responses=True
            )
            self.cache.ping()
            logger.info("✅ Redis cache initialized")

        except Exception as e:
            logger.warning(f"⚠️ Redis not available: {e}")
            self.cache = None

    def store(self, text: str, memory_type: str = "conversation", metadata: Dict = None):
        """
        Store memory across all subsystems
        - GraphRAG: Extract entities and relationships
        - ColBERT: Add to retrieval index
        - Cache: Store recent items
        """
        logger.info(f"💾 Storing memory: {memory_type} - {text[:50]}...")

        metadata = metadata or {}
        metadata["timestamp"] = datetime.now().isoformat()
        metadata["type"] = memory_type

        # Store in GraphRAG
        if self.graph_rag:
            try:
                self.graph_rag.add_to_graph(text, metadata)
            except Exception as e:
                logger.error(f"❌ GraphRAG storage failed: {e}")

        # Store in ColBERT
        if self.colbert:
            try:
                self.colbert.add_documents([text], [metadata])
            except Exception as e:
                logger.error(f"❌ ColBERT storage failed: {e}")

        # Store in cache
        if self.cache:
            try:
                cache_key = f"memory:{memory_type}:{datetime.now().timestamp()}"
                cache_value = json.dumps({"text": text, "metadata": metadata})
                self.cache.setex(cache_key, 3600, cache_value)  # 1 hour TTL
            except Exception as e:
                logger.error(f"❌ Cache storage failed: {e}")

        logger.info("✅ Memory stored")

    def store_agent_result(self, task_description: str, result: Dict[str, Any], agent_name: str = None):
        """
        Store the result of an agent's execution for learning and reference

        Args:
            task_description: Description of the task that was executed
            result: Result dictionary from the agent execution
            agent_name: Name of the agent that executed the task
        """
        logger.info(f"💾 Storing agent result for task: {task_description[:50]}...")

        metadata = {
            "timestamp": datetime.now().isoformat(),
            "type": "agent_result",
            "agent_name": agent_name or "unknown",
            "task_description": task_description,
            "success": result.get('success', False),
            "execution_time": result.get('execution_time', 0)
        }

        # Store in GraphRAG
        if self.graph_rag:
            try:
                self.graph_rag.add_to_graph(task_description, metadata)
            except Exception as e:
                logger.error(f"❌ GraphRAG storage failed: {e}")

        # Store in ColBERT
        if self.colbert:
            try:
                text_to_store = f"Task: {task_description}\nResult: {json.dumps(result, indent=2)[:500]}"  # Limit length
                self.colbert.add_documents([text_to_store], [metadata])
            except Exception as e:
                logger.error(f"❌ ColBERT storage failed: {e}")

        # Store in cache
        if self.cache:
            try:
                cache_key = f"agent_result:{agent_name}:{datetime.now().timestamp()}"
                cache_value = json.dumps({
                    "task_description": task_description,
                    "result": result,
                    "metadata": metadata
                })
                self.cache.setex(cache_key, 3600, cache_value)  # 1 hour TTL
            except Exception as e:
                logger.error(f"❌ Cache storage failed: {e}")

        logger.info("✅ Agent result stored")

    def retrieve(self, query: str, top_k: int = 5, memory_type: str = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories
        Uses ColBERT for precise retrieval
        """
        logger.info(f"🔍 Retrieving memories for: {query[:50]}...")

        results = []

        # Retrieve from ColBERT
        if self.colbert:
            try:
                colbert_results = self.colbert.retrieve(query, top_k=top_k)
                results.extend(colbert_results)
            except Exception as e:
                logger.error(f"❌ ColBERT retrieval failed: {e}")

        # Filter by type if specified
        if memory_type:
            results = [r for r in results if r.get("metadata", {}).get("type") == memory_type]

        logger.info(f"✅ Retrieved {len(results)} memories")
        return results[:top_k]

    def query_graph(self, question: str) -> str:
        """
        Query knowledge graph for global questions
        Examples:
        - "What are the themes of my projects?"
        - "How are X and Y related?"
        """
        if not self.graph_rag:
            return "GraphRAG not available"

        try:
            return self.graph_rag.query(question)
        except Exception as e:
            logger.error(f"❌ Graph query failed: {e}")
            return f"Error: {str(e)}"

    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics"""
        stats = {
            "timestamp": datetime.now().isoformat(),
            "graph_rag": self.graph_rag.get_stats() if self.graph_rag else None,
            "colbert": self.colbert.get_stats() if self.colbert else None,
            "cache_available": self.cache is not None
        }

        return stats

    def save_all(self):
        """Save all memory subsystems to disk"""
        logger.info("💾 Saving all memory systems...")

        # Save GraphRAG
        if self.graph_rag:
            try:
                graph_file = os.path.join(self.storage_path, "knowledge_graph.json")
                self.graph_rag.save(graph_file)
            except Exception as e:
                logger.error(f"❌ GraphRAG save failed: {e}")

        # Save ColBERT
        if self.colbert:
            try:
                colbert_file = os.path.join(self.storage_path, "colbert_docs.json")
                self.colbert.save(colbert_file)
            except Exception as e:
                logger.error(f"❌ ColBERT save failed: {e}")

        logger.info("✅ All memory systems saved")

    def clear_cache(self):
        """Clear Redis cache"""
        if self.cache:
            try:
                self.cache.flushdb()
                logger.info("🗑️ Cache cleared")
            except Exception as e:
                logger.error(f"❌ Cache clear failed: {e}")


# Test
if __name__ == "__main__":
    controller = MemoryController()

    # Test storage
    controller.store("I'm working on JARVIS v9.0 with GraphRAG and ColBERT", "project")
    controller.store("JARVIS uses FastAPI for the backend", "technical")
    controller.store("Need to implement speculative decoding for faster inference", "todo")

    # Test retrieval
    print("\n" + "="*50)
    print("RETRIEVAL TEST")
    print("="*50)

    results = controller.retrieve("How does JARVIS work?", top_k=3)
    for i, result in enumerate(results, 1):
        print(f"{i}. [{result['score']:.3f}] {result['text']}")

    # Test graph query
    print("\n" + "="*50)
    print("GRAPH QUERY TEST")
    print("="*50)

    print(controller.query_graph("What are the themes of my projects?"))

    # Stats
    print("\n" + "="*50)
    print("STATS")
    print("="*50)
    print(json.dumps(controller.get_stats(), indent=2))

    # Save
    controller.save_all()

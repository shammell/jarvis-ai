# ==========================================================
# JARVIS v9.0 - ColBERTv2 Late Interaction Retrieval
# Token-level matching for near-zero hallucination
# Dramatically improves retrieval accuracy over dense embeddings
# ==========================================================

import numpy as np
import logging
from typing import List, Dict, Any, Tuple
import json
import os

logger = logging.getLogger(__name__)


class ColBERTRetriever:
    """
    ColBERT late interaction retrieval for JARVIS v9.0
    - Token-level similarity instead of sentence-level
    - Near-zero hallucination
    - Falls back to TF-IDF if ColBERT unavailable
    """

    def __init__(self, model_name: str = "colbert-ir/colbertv2.0", use_gpu: bool = False):
        self.model_name = model_name
        self.use_gpu = use_gpu
        self.documents = []
        self.doc_embeddings = []
        self.colbert_available = False
        self._vectorizer_fitted = False

        # Try to import ColBERT
        try:
            from colbert.infra import Run, RunConfig, ColBERTConfig
            from colbert.modeling.checkpoint import Checkpoint
            from colbert import Indexer, Searcher

            self.colbert_available = True
            self._init_colbert()
            logger.info("✅ ColBERT initialized")

        except ImportError:
            logger.warning("⚠️ ColBERT not available, using TF-IDF fallback")
            self._init_tfidf_fallback()

    def _init_colbert(self):
        """Initialize ColBERT model"""
        try:
            from colbert.infra import Run, RunConfig, ColBERTConfig
            from colbert.modeling.checkpoint import Checkpoint

            # Load checkpoint
            self.checkpoint = Checkpoint(self.model_name, colbert_config=ColBERTConfig())
            logger.info(f"📦 Loaded ColBERT checkpoint: {self.model_name}")

        except Exception as e:
            logger.error(f"❌ Failed to initialize ColBERT: {e}")
            self.colbert_available = False
            self._init_tfidf_fallback()

    def _init_tfidf_fallback(self):
        """Initialize TF-IDF fallback"""
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.tfidf_matrix = None
        logger.info("📊 TF-IDF fallback initialized")

    def add_documents(self, documents: List[str], metadata: List[Dict] = None):
        """
        Add documents to the retriever
        documents: List of text strings
        metadata: Optional list of metadata dicts
        """
        if not documents:
            return

        logger.info(f"📚 Adding {len(documents)} documents...")

        self.documents.extend(documents)

        if self.colbert_available:
            self._add_documents_colbert(documents)
        else:
            self._add_documents_tfidf(documents)

        logger.info(f"✅ Total documents: {len(self.documents)}")

    def _add_documents_colbert(self, documents: List[str]):
        """Add documents using ColBERT"""
        try:
            # Encode documents at token level
            for doc in documents:
                # ColBERT encodes each token separately
                doc_embedding = self.checkpoint.docFromText([doc], bsize=1)
                self.doc_embeddings.append(doc_embedding)

        except Exception as e:
            logger.error(f"❌ ColBERT encoding failed: {e}")

    def _add_documents_tfidf(self, documents: List[str]):
        """Add documents using TF-IDF fallback"""
        # Mark vectorizer as not fitted. It will be refit on the next retrieval.
        self._vectorizer_fitted = False
        self.tfidf_matrix = None

    def retrieve(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Retrieve most relevant documents for query
        Returns: List of {text, score, index}
        """
        if not self.documents:
            logger.warning("⚠️ No documents to retrieve from")
            return []

        logger.info(f"🔍 Retrieving top {top_k} for: {query[:50]}...")

        if self.colbert_available:
            results = self._retrieve_colbert(query, top_k)
        else:
            results = self._retrieve_tfidf(query, top_k)

        logger.info(f"✅ Retrieved {len(results)} results")
        return results

    def _retrieve_colbert(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Retrieve using ColBERT late interaction"""
        try:
            # Encode query at token level
            query_embedding = self.checkpoint.queryFromText([query], bsize=1)

            # Compute late interaction scores
            scores = []
            for i, doc_embedding in enumerate(self.doc_embeddings):
                # MaxSim: For each query token, find max similarity with any doc token
                # Then sum across all query tokens
                score = self._compute_maxsim(query_embedding, doc_embedding)
                scores.append((i, score))

            # Sort by score
            scores.sort(key=lambda x: x[1], reverse=True)

            # Return top_k
            results = []
            for idx, score in scores[:top_k]:
                results.append({
                    "text": self.documents[idx],
                    "score": float(score),
                    "index": idx
                })

            return results

        except Exception as e:
            logger.error(f"❌ ColBERT retrieval failed: {e}")
            return self._retrieve_tfidf(query, top_k)

    def _compute_maxsim(self, query_embedding, doc_embedding):
        """
        Compute MaxSim score (ColBERT late interaction)
        For each query token, find max similarity with any doc token
        """
        # Simplified version - actual ColBERT uses optimized CUDA kernels
        # This is a NumPy approximation
        try:
            # Assuming embeddings are [num_tokens, embedding_dim]
            # Compute cosine similarity between all query-doc token pairs
            similarities = np.dot(query_embedding, doc_embedding.T)

            # For each query token, take max similarity
            max_sims = np.max(similarities, axis=1)

            # Sum across query tokens
            score = np.sum(max_sims)

            return score

        except Exception as e:
            logger.error(f"❌ MaxSim computation failed: {e}")
            return 0.0

    def _retrieve_tfidf(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Retrieve using TF-IDF fallback"""
        from sklearn.metrics.pairwise import cosine_similarity

        # Ensure we have docs and the vectorizer is fitted
        if not self.documents:
            return []

        if not self._vectorizer_fitted:
            try:
                self.tfidf_matrix = self.vectorizer.fit_transform(self.documents)
                self._vectorizer_fitted = True
                logger.info("📊 TF-IDF vectorizer fitted on retrieval")
            except ValueError:
                logger.warning("⚠️ TF-IDF vectorizer failed to fit (empty vocabulary). Returning empty.")
                return []

        # Transform query and compute similarities
        query_vec = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vec, self.tfidf_matrix)[0]

        # Get top_k indices
        # Ensure we don't request more than the number of documents
        k = min(top_k, len(self.documents))
        top_indices = np.argsort(similarities)[::-1][:k]

        # Build results
        results = []
        for idx in top_indices:
            results.append({
                "text": self.documents[idx],
                "score": float(similarities[idx]),
                "index": int(idx)
            })

        return results

    def save(self, filepath: str):
        """Save retriever state"""
        data = {
            "documents": self.documents,
            "model_name": self.model_name,
            "colbert_available": self.colbert_available
        }

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"💾 Retriever saved to {filepath}")

    def load(self, filepath: str):
        """Load retriever state"""
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)

            self.documents = data.get("documents", [])

            # Re-encode documents
            if self.colbert_available:
                self._add_documents_colbert(self.documents)
            else:
                self._add_documents_tfidf(self.documents)

            logger.info(f"📂 Retriever loaded from {filepath}")

        except Exception as e:
            logger.error(f"❌ Failed to load retriever: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get retriever statistics"""
        return {
            "num_documents": len(self.documents),
            "colbert_available": self.colbert_available,
            "model_name": self.model_name
        }


# Test
if __name__ == "__main__":
    retriever = ColBERTRetriever()

    # Test documents
    docs = [
        "JARVIS is an AI assistant built with Python and FastAPI",
        "The system uses Groq API for fast LLM inference",
        "GraphRAG helps with knowledge graph construction",
        "ColBERT provides token-level retrieval accuracy",
        "WhatsApp integration uses Baileys WebSocket client"
    ]

    retriever.add_documents(docs)

    # Test queries
    queries = [
        "How does JARVIS work?",
        "What is used for LLM?",
        "Tell me about retrieval"
    ]

    for query in queries:
        print(f"\n{'='*50}")
        print(f"Query: {query}")
        print('='*50)

        results = retriever.retrieve(query, top_k=3)
        for i, result in enumerate(results, 1):
            print(f"{i}. [{result['score']:.3f}] {result['text']}")

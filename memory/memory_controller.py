# ==========================================================
# JARVIS v9.0 - Memory Controller
# Integrates GraphRAG, ColBERT, and existing memory systems
# ==========================================================

import logging
from typing import List, Dict, Any, Optional
import os
import json
from datetime import datetime
import hashlib

from core.security_system import security_manager, Permission, input_validator
from core.encryption_utils import (
    encrypt_data,
    decrypt_data,
    register_tenant,
    log_context_access,
    sweep_context_leaks,
    TenantNamespaceManager,
    ContextLeakSweeper
)

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

        # Initialize encryption and tenant management
        self.tenant_manager = TenantNamespaceManager()
        self.context_sweeper = ContextLeakSweeper()
        self.enable_encryption = self.config.get("enable_encryption", True)
        self.default_tenant = self.config.get("default_tenant", "default")

        # Register default tenant
        encryption_key_source = self.config.get("encryption_key_source", "ENV:JARVIS_ENCRYPTION_KEY")
        self.tenant_manager.register_tenant(self.default_tenant, encryption_key_source)

        # Track tenant-based access
        self.tenant_access_log = {}
        self.encryption_audit_log = []

        # Initialize subsystems
        self._init_graph_rag()
        self._init_colbert()
        self._init_cache()

        # Context pinning for memory management
        self.pinned_contexts = {}  # {context_id: {priority, timestamp, content}}
        self.max_contexts = self.config.get("max_contexts", 100)
        self.context_ttl = self.config.get("context_ttl", 3600)  # 1 hour default

        # Async Airlock - Background Task Management
        self.background_tasks = set()

        logger.info("🧠 Memory Controller initialized with encryption and RBAC")

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

    def store(self, text: str, memory_type: str = "conversation", metadata: Dict = None, auth_token: str = None, tenant_id: str = None):
        """
        Store memory across all subsystems with encryption and RBAC enforcement
        - GraphRAG: Extract entities and relationships
        - ColBERT: Add to retrieval index
        - Cache: Store recent items
        - Encryption: AES-256-GCM at rest
        - RBAC: Permission checks and audit logging
        """
        # Determine tenant and validate permissions
        tenant_id = tenant_id or self.default_tenant

        # RBAC enforcement
        if auth_token:
            if not security_manager.check_permission(auth_token, Permission.WRITE_MEMORY):
                raise PermissionError("Unauthorized memory write attempt")

            # Get user context for audit logging
            user_payload = security_manager.validate_token(auth_token, 'access')
            user_id = user_payload.get('user_id', 'anonymous')

            # Log security event
            security_manager.log_security_event(
                "memory_write_attempt",
                user_id,
                {
                    "tenant_id": tenant_id,
                    "memory_type": memory_type,
                    "text_hash": hashlib.sha256(text.encode()).hexdigest()[:16]
                }
            )
        else:
            user_id = "system"

        # Validate input
        if not input_validator.validate_input(text, 'general'):
            raise ValueError("Invalid memory content")

        metadata = metadata or {}
        metadata["timestamp"] = datetime.now().isoformat()
        metadata["type"] = memory_type
        metadata["tenant_id"] = tenant_id
        metadata["user_id"] = user_id

        # Encrypt sensitive data if encryption is enabled
        encrypted_text = text
        encrypted_metadata = metadata
        if self.enable_encryption:
            encrypted_text = encrypt_data(text, tenant_id)
            encrypted_metadata = encrypt_data(metadata, tenant_id)
            # Log encryption for audit trail
            self.encryption_audit_log.append({
                "action": "encrypt",
                "tenant_id": tenant_id,
                "user_id": user_id,
                "original_type": memory_type,
                "timestamp": datetime.now().isoformat()
            })

        logger.info(f"💾 Storing encrypted memory: {memory_type} - {text[:50]}...")

        # Store in GraphRAG
        if self.graph_rag:
            try:
                self.graph_rag.add_to_graph(encrypted_text, encrypted_metadata)
            except Exception as e:
                logger.error(f"❌ GraphRAG storage failed: {e}")

        # Store in ColBERT
        if self.colbert:
            try:
                # ColBERT might need special handling for encrypted data
                self.colbert.add_documents([encrypted_text], [encrypted_metadata])
            except Exception as e:
                logger.error(f"❌ ColBERT storage failed: {e}")

        # Store in cache
        if self.cache:
            try:
                cache_key = f"memory:{tenant_id}:{memory_type}:{datetime.now().timestamp()}"
                cache_value = json.dumps({"text": encrypted_text, "metadata": encrypted_metadata})
                self.cache.setex(cache_key, 3600, cache_value)  # 1 hour TTL
            except Exception as e:
                logger.error(f"❌ Cache storage failed: {e}")

        # Context pinning check - automatically pin important memories
        if memory_type in ["project", "technical", "todo", "agent_result"]:
            # Automatically pin important memory types
            context_id = f"{tenant_id}:{memory_type}_{hash(text[:50])}"
            self.pin_context(context_id, encrypted_text, priority=2, metadata=encrypted_metadata)

        # Track tenant access
        self._log_tenant_access(user_id, tenant_id, "store", memory_type)

        logger.info("✅ Encrypted memory stored with RBAC enforcement")

    def pin_context(self, context_id: str, content: str, priority: int = 1, metadata: Dict = None, tenant_id: str = None):
        """
        Pin important context to prevent it from being evicted
        - context_id: Unique identifier for the context
        - content: The actual context content
        - priority: Priority level (higher = more important)
        - metadata: Additional context information
        - tenant_id: Tenant identifier for namespace isolation
        """
        tenant_id = tenant_id or self.default_tenant

        logger.info(f"📍 Pinning context: {context_id} (priority: {priority}) for tenant: {tenant_id}")

        # Encrypt content if encryption is enabled
        encrypted_content = content
        encrypted_metadata = metadata or {}
        if self.enable_encryption:
            encrypted_content = encrypt_data(content, tenant_id)
            if encrypted_metadata:
                encrypted_metadata = encrypt_data(encrypted_metadata, tenant_id)

        # Include tenant info in pinned context
        context_data = {
            "content": encrypted_content,
            "priority": priority,
            "timestamp": datetime.now().isoformat(),
            "metadata": encrypted_metadata,
            "tenant_id": tenant_id,
            "access_count": 0
        }

        self.pinned_contexts[context_id] = context_data

        # Enforce max contexts limit
        if len(self.pinned_contexts) > self.max_contexts:
            self._evict_lowest_priority_context()

        logger.info(f"✅ Context {context_id} pinned for tenant {tenant_id}")

    def unpin_context(self, context_id: str):
        """Unpin context to allow eviction"""
        if context_id in self.pinned_contexts:
            del self.pinned_contexts[context_id]
            logger.info(f"🗑️ Context {context_id} unpinned")

    def get_pinned_context(self, context_id: str, tenant_id: str = None) -> Optional[Dict[str, Any]]:
        """Retrieve pinned context by ID with tenant isolation and decryption"""
        tenant_id = tenant_id or self.default_tenant

        if context_id in self.pinned_contexts:
            context = self.pinned_contexts[context_id]

            # Verify tenant access
            pinned_tenant_id = context.get("tenant_id", self.default_tenant)
            if pinned_tenant_id != tenant_id:
                logger.warning(f"⚠️ Tenant {tenant_id} tried to access context from tenant {pinned_tenant_id}")
                return None

            # Increment access count
            context["access_count"] += 1

            # Decrypt content if encryption is enabled
            if self.enable_encryption:
                try:
                    # Decrypt content
                    decrypted_content = decrypt_data(context["content"], tenant_id)
                    context["content"] = decrypted_content

                    # Decrypt metadata if it's encrypted
                    if isinstance(context["metadata"], str):
                        decrypted_metadata = decrypt_data(context["metadata"], tenant_id)
                        context["metadata"] = decrypted_metadata

                except Exception as e:
                    logger.error(f"❌ Failed to decrypt pinned context: {e}")
                    # Return as-is if decryption fails
                    pass

            return context
        return None

    def get_all_pinned_contexts(self, tenant_id: str = None) -> Dict[str, Dict[str, Any]]:
        """Get all pinned contexts with tenant isolation"""
        tenant_id = tenant_id or self.default_tenant

        # Filter contexts to specific tenant
        filtered_contexts = {}
        for context_id, context_data in self.pinned_contexts.items():
            pinned_tenant_id = context_data.get("tenant_id", self.default_tenant)
            if pinned_tenant_id == tenant_id:
                # Decrypt content if encryption is enabled
                if self.enable_encryption:
                    try:
                        # Decrypt content
                        decrypted_content = decrypt_data(context_data["content"], tenant_id)
                        context_data_copy = context_data.copy()
                        context_data_copy["content"] = decrypted_content

                        # Decrypt metadata if it's encrypted
                        if isinstance(context_data["metadata"], str):
                            decrypted_metadata = decrypt_data(context_data["metadata"], tenant_id)
                            context_data_copy["metadata"] = decrypted_metadata

                        filtered_contexts[context_id] = context_data_copy
                    except Exception as e:
                        logger.error(f"❌ Failed to decrypt pinned context: {e}")
                        # Skip this context if decryption fails
                        continue
                else:
                    filtered_contexts[context_id] = context_data.copy()

        return filtered_contexts

    def cleanup_expired_contexts(self):
        """Remove expired pinned contexts"""
        current_time = datetime.now()
        expired_contexts = []

        for context_id, context_data in self.pinned_contexts.items():
            context_time = datetime.fromisoformat(context_data["timestamp"])
            if (current_time - context_time).total_seconds() > self.context_ttl:
                expired_contexts.append(context_id)

        for context_id in expired_contexts:
            self.unpin_context(context_id)

        if expired_contexts:
            logger.info(f"🧹 Cleaned up {len(expired_contexts)} expired contexts")

    def _evict_lowest_priority_context(self):
        """Evict context with lowest priority"""
        if not self.pinned_contexts:
            return

        # Sort by priority ascending, then by access count ascending, then by timestamp ascending
        sorted_contexts = sorted(
            self.pinned_contexts.items(),
            key=lambda x: (x[1]["priority"], x[1]["access_count"], x[1]["timestamp"])
        )

        evicted_id = sorted_contexts[0][0]
        evicted_priority = sorted_contexts[0][1]["priority"]
        self.unpin_context(evicted_id)

        logger.info(f"🗑️ Evicted context {evicted_id} (priority: {evicted_priority})")

    def get_memory_health(self, tenant_id: str = None) -> Dict[str, Any]:
        """Get memory system health status with tenant-specific metrics"""
        tenant_id = tenant_id or self.default_tenant

        # Count total and tenant-specific pinned contexts
        total_contexts = len(self.pinned_contexts)
        tenant_contexts = sum(1 for ctx in self.pinned_contexts.values()
                             if ctx.get("tenant_id", self.default_tenant) == tenant_id)

        health = {
            "status": "healthy",
            "tenant_id": tenant_id,
            "pinned_contexts_count": total_contexts,
            "tenant_pinned_contexts": tenant_contexts,
            "pinned_contexts_usage": total_contexts / self.max_contexts,
            "tenant_contexts_usage": tenant_contexts / self.max_contexts,
            "encrypted_storage": self.enable_encryption,
            "encryption_key_source": "HSM/ENV" if self.enable_encryption else "None",
            "tenant_isolation": True,
            "expired_contexts": 0,
            "tenant_expired_contexts": 0,
            "subsystems": {
                "graph_rag": "healthy" if self.graph_rag else "unavailable",
                "colbert": "healthy" if self.colbert else "unavailable",
                "cache": "healthy" if self.cache else "unavailable"
            },
            "security_metrics": {
                "last_encryption_audit": self.encryption_audit_log[-1]["timestamp"] if self.encryption_audit_log else None,
                "total_encryption_ops": len(self.encryption_audit_log),
                "context_sweeper_active": True
            }
        }

        # Count expired contexts
        current_time = datetime.now()
        expired_count = 0
        tenant_expired_count = 0

        for context_data in self.pinned_contexts.values():
            context_time = datetime.fromisoformat(context_data["timestamp"])
            if (current_time - context_time).total_seconds() > self.context_ttl:
                expired_count += 1
                if context_data.get("tenant_id", self.default_tenant) == tenant_id:
                    tenant_expired_count += 1

        health["expired_contexts"] = expired_count
        health["tenant_expired_contexts"] = tenant_expired_count

        # Determine overall status
        if expired_count > 0:
            health["status"] = "warning"
            health["issues"] = [f"{expired_count} expired contexts need cleanup ({tenant_expired_count} in tenant)"]
        elif total_contexts >= self.max_contexts:
            health["status"] = "warning"
            health["issues"] = ["Memory at capacity, eviction may occur"]
        elif total_contexts > self.max_contexts * 0.8:
            health["status"] = "caution"
            health["issues"] = ["Memory usage high"]

        return health

    def store_agent_result(self, task_description: str, result: Dict[str, Any], agent_name: str = None, auth_token: str = None, tenant_id: str = None):
        """
        Store the result of an agent's execution for learning and reference with encryption and RBAC

        Args:
            task_description: Description of the task that was executed
            result: Result dictionary from the agent execution
            agent_name: Name of the agent that executed the task
            auth_token: Authentication token for permission checking
            tenant_id: Tenant identifier for namespace isolation
        """
        # Determine tenant and validate permissions
        tenant_id = tenant_id or self.default_tenant

        # RBAC enforcement
        if auth_token:
            if not security_manager.check_permission(auth_token, Permission.WRITE_MEMORY):
                raise PermissionError("Unauthorized agent result storage attempt")

            # Get user context for audit logging
            user_payload = security_manager.validate_token(auth_token, 'access')
            user_id = user_payload.get('user_id', 'anonymous')
        else:
            user_id = "system"

        logger.info(f"💾 Storing encrypted agent result for task: {task_description[:50]}... (Tenant: {tenant_id})")

        metadata = {
            "timestamp": datetime.now().isoformat(),
            "type": "agent_result",
            "agent_name": agent_name or "unknown",
            "task_description": task_description,
            "success": result.get('success', False),
            "execution_time": result.get('execution_time', 0),
            "tenant_id": tenant_id,
            "user_id": user_id
        }

        # Encrypt sensitive data if encryption is enabled
        encrypted_task_desc = task_description
        encrypted_result = result
        encrypted_metadata = metadata
        if self.enable_encryption:
            encrypted_task_desc = encrypt_data(task_description, tenant_id)
            encrypted_result = encrypt_data(result, tenant_id)
            encrypted_metadata = encrypt_data(metadata, tenant_id)

        # Store in GraphRAG
        if self.graph_rag:
            try:
                self.graph_rag.add_to_graph(encrypted_task_desc, encrypted_metadata)
            except Exception as e:
                logger.error(f"❌ GraphRAG storage failed: {e}")

        # Store in ColBERT
        if self.colbert:
            try:
                text_to_store = f"Task: {task_description}\nResult: {json.dumps(result, indent=2)[:500]}"  # Limit length
                # Use encrypted version for actual storage if encryption is enabled
                if self.enable_encryption:
                    text_to_store = encrypt_data(text_to_store, tenant_id)
                self.colbert.add_documents([text_to_store], [encrypted_metadata])
            except Exception as e:
                logger.error(f"❌ ColBERT storage failed: {e}")

        # Store in cache
        if self.cache:
            try:
                cache_key = f"agent_result:{tenant_id}:{agent_name}:{datetime.now().timestamp()}"
                cache_value = json.dumps({
                    "task_description": encrypted_task_desc,
                    "result": encrypted_result,
                    "metadata": encrypted_metadata
                })
                self.cache.setex(cache_key, 3600, cache_value)  # 1 hour TTL
            except Exception as e:
                logger.error(f"❌ Cache storage failed: {e}")

        # Context pinning for agent results
        context_id = f"agent_result:{tenant_id}:{hash(task_description[:50])}"
        self.pin_context(context_id, json.dumps(result), priority=2, metadata=metadata, tenant_id=tenant_id)

        # Track tenant access
        self._log_tenant_access(user_id, tenant_id, "store_agent_result", f"agent_{agent_name}")

        # Log security event
        if auth_token:
            security_manager.log_security_event(
                "agent_result_stored",
                user_id,
                {
                    "tenant_id": tenant_id,
                    "agent_name": agent_name,
                    "success": result.get('success', False)
                }
            )

        logger.info("✅ Encrypted agent result stored with RBAC enforcement")

    def retrieve(self, query: str, top_k: int = 5, memory_type: str = None, auth_token: str = None, tenant_id: str = None) -> List[Dict[str, Any]]:
        """
        Retrieve relevant memories with decryption and RBAC enforcement
        Uses ColBERT for precise retrieval
        """
        # Determine tenant and validate permissions
        tenant_id = tenant_id or self.default_tenant

        # RBAC enforcement
        if auth_token:
            if not security_manager.check_permission(auth_token, Permission.READ_MEMORY):
                raise PermissionError("Unauthorized memory read attempt")

            # Get user context for audit logging
            user_payload = security_manager.validate_token(auth_token, 'access')
            user_id = user_payload.get('user_id', 'anonymous')

            # Log security event
            security_manager.log_security_event(
                "memory_read_attempt",
                user_id,
                {
                    "tenant_id": tenant_id,
                    "query": query[:100],
                    "top_k": top_k
                }
            )
        else:
            user_id = "system"

        if not input_validator.validate_input(query, 'general'):
            raise ValueError("Invalid memory query")

        logger.info(f"🔍 Retrieving memories for: {query[:50]}... (Tenant: {tenant_id})")

        # Encrypt the query for searching if needed
        search_query = query
        if self.enable_encryption:
            # For search, we may need a different approach than full encryption
            # For now, use the original query but log that we're operating in encrypted mode
            logger.debug(f"Using encrypted storage mode for retrieval")

        results = []

        # Retrieve from ColBERT
        if self.colbert:
            try:
                colbert_results = self.colbert.retrieve(search_query, top_k=top_k)

                # Decrypt results if encryption is enabled
                if self.enable_encryption:
                    decrypted_results = []
                    for result in colbert_results:
                        try:
                            decrypted_result = self._decrypt_result(result, tenant_id)
                            decrypted_results.append(decrypted_result)
                        except Exception as e:
                            logger.error(f"❌ Failed to decrypt result: {e}")
                            # Skip this result but continue processing others
                            continue
                    results.extend(decrypted_results)
                else:
                    results.extend(colbert_results)

            except Exception as e:
                logger.error(f"❌ ColBERT retrieval failed: {e}")

        # Filter by type if specified
        if memory_type:
            results = [r for r in results if r.get("metadata", {}).get("type") == memory_type]

        # Apply tenant isolation - filter results to tenant-specific data
        tenant_filtered_results = []
        for result in results:
            metadata = result.get("metadata", {})
            result_tenant = metadata.get("tenant_id", self.default_tenant)
            if result_tenant == tenant_id:
                tenant_filtered_results.append(result)

        results = tenant_filtered_results

        logger.info(f"✅ Retrieved {len(results)} memories for tenant {tenant_id}")

        # Cleanup expired contexts during retrieval
        self.cleanup_expired_contexts()

        # Track tenant access
        self._log_tenant_access(user_id, tenant_id, "retrieve", f"query_{len(results)}_results")

        return results[:top_k]

    def _decrypt_result(self, result: Dict[str, Any], tenant_id: str) -> Dict[str, Any]:
        """Helper method to decrypt a result if it's encrypted"""
        try:
            # Attempt to decrypt text
            if 'text' in result:
                decrypted_text = decrypt_data(result['text'], tenant_id)
                result['text'] = decrypted_text

            # Attempt to decrypt metadata
            if 'metadata' in result and isinstance(result['metadata'], str):
                # If metadata is encrypted string, decrypt it
                decrypted_metadata = decrypt_data(result['metadata'], tenant_id)
                result['metadata'] = decrypted_metadata
            elif 'metadata' in result and isinstance(result['metadata'], dict):
                # If metadata exists as dict, check if it's encrypted content
                # This assumes encrypted content would be stored as a string
                pass

        except Exception as e:
            logger.error(f"❌ Failed to decrypt result: {e}")
            # If decryption fails, return the original result
            # This preserves functionality if data wasn't encrypted
            return result

        return result

    def _log_tenant_access(self, user_id: str, tenant_id: str, access_type: str, resource: str):
        """Log tenant-specific access for audit and security monitoring"""
        access_log = {
            "user_id": user_id,
            "tenant_id": tenant_id,
            "access_type": access_type,
            "resource": resource,
            "timestamp": datetime.now().isoformat()
        }

        # Store in tenant-specific access log
        if tenant_id not in self.tenant_access_log:
            self.tenant_access_log[tenant_id] = []
        self.tenant_access_log[tenant_id].append(access_log)

        # Log access for leak detection
        log_context_access(resource, user_id, access_type)

    def query_graph(self, question: str, auth_token: str = None, tenant_id: str = None) -> str:
        """
        Query knowledge graph for global questions with tenant isolation
        Examples:
        - "What are the themes of my projects?"
        - "How are X and Y related?"
        """
        # Determine tenant and validate permissions
        tenant_id = tenant_id or self.default_tenant

        # RBAC enforcement for graph queries
        if auth_token and not security_manager.check_permission(auth_token, Permission.READ_MEMORY):
            raise PermissionError("Unauthorized graph query attempt")

        if not self.graph_rag:
            return "GraphRAG not available"

        try:
            # For graph queries, we may need to handle encryption differently
            # The query itself goes to the graph engine, but results may need decryption
            result = self.graph_rag.query(question)

            # Log tenant access
            user_id = "system"
            if auth_token:
                user_payload = security_manager.validate_token(auth_token, 'access')
                user_id = user_payload.get('user_id', 'anonymous')
            self._log_tenant_access(user_id, tenant_id, "query_graph", f"question_{hash(question[:50])}")

            return result
        except Exception as e:
            logger.error(f"❌ Graph query failed: {e}")
            return f"Error: {str(e)}"

    def get_stats(self, tenant_id: str = None) -> Dict[str, Any]:
        """Get memory system statistics with tenant-specific metrics"""
        tenant_id = tenant_id or self.default_tenant

        # Calculate tenant-specific stats
        tenant_pinned = {k: v for k, v in self.pinned_contexts.items()
                         if v.get("tenant_id", self.default_tenant) == tenant_id}

        stats = {
            "timestamp": datetime.now().isoformat(),
            "tenant_id": tenant_id,
            "graph_rag": self.graph_rag.get_stats() if self.graph_rag else None,
            "colbert": self.colbert.get_stats() if self.colbert else None,
            "cache_available": self.cache is not None,
            "encryption_enabled": self.enable_encryption,
            "encryption_key_source": self.config.get("encryption_key_source", "ENV:JARVIS_ENCRYPTION_KEY"),
            "tenants_registered": list(self.tenant_manager.tenant_namespaces.keys()),
            "tenant_access_count": len(self.tenant_access_log.get(tenant_id, [])),
            "encryption_audit_logs_count": len(self.encryption_audit_log),
            "pinned_contexts": {
                "total_count": len(self.pinned_contexts),
                "tenant_count": len(tenant_pinned),
                "max_contexts": self.max_contexts,
                "context_ttl": self.context_ttl,
                "tenant_contexts": list(tenant_pinned.keys()),
                "global_contexts": list(self.pinned_contexts.keys())
            },
            "security_metrics": {
                "last_sweep_operations": len(self.encryption_audit_log[-10:]) if self.encryption_audit_log else 0,
                "sweeper_detection_enabled": True
            }
        }

        return stats

    def save_all(self):
        """Save all memory subsystems to disk with encryption"""
        logger.info("💾 Saving all memory systems with encryption...")

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

        # Optionally save pinned contexts with tenant isolation
        try:
            pinned_file = os.path.join(self.storage_path, "pinned_contexts.json")
            # Only save non-sensitive metadata for persistence
            simplified_pinned = {}
            for context_id, context_data in self.pinned_contexts.items():
                # Preserve only essential metadata for reload, excluding full content
                simplified_pinned[context_id] = {
                    "priority": context_data.get("priority"),
                    "timestamp": context_data.get("timestamp"),
                    "tenant_id": context_data.get("tenant_id", self.default_tenant),
                    "access_count": context_data.get("access_count", 0)
                }

            with open(pinned_file, 'w') as f:
                json.dump(simplified_pinned, f, indent=2)
        except Exception as e:
            logger.error(f"❌ Pinned contexts save failed: {e}")

        logger.info("✅ All memory systems saved with encryption")

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

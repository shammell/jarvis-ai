"""
==========================================================
JARVIS - Central Heartbeat Registry
==========================================================
Tracks all initialized modules, their health, and metadata.
Converts disconnected islands into a structural master DAG.
==========================================================
"""

import logging
import threading
from typing import Dict, Any, List, Optional, Type, Callable
from datetime import datetime

logger = logging.getLogger(__name__)

class SystemRegistry:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return
        self.modules: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.Lock()
        self._initialized = True
        logger.info("💓 System Registry (Heartbeat) initialized")

    def register(self, module_name: str, module_obj: Any, metadata: Dict[str, Any] = None):
        """Register a module instance with metadata"""
        with self._lock:
            self.modules[module_name] = {
                "instance": module_obj,
                "type": type(module_obj).__name__,
                "registered_at": datetime.now().isoformat(),
                "status": "healthy",
                "metadata": metadata or {}
            }
            logger.info(f"✅ Registered: {module_name} [{type(module_obj).__name__}]")

    def get_module(self, name: str) -> Optional[Any]:
        return self.modules.get(name, {}).get("instance")

    def update_status(self, name: str, status: str):
        with self._lock:
            if name in self.modules:
                self.modules[name]["status"] = status

    def get_all_registered(self) -> List[str]:
        return list(self.modules.keys())

    def get_registry_stats(self) -> Dict[str, Any]:
        return {
            "total_modules": len(self.modules),
            "healthy": len([m for m in self.modules.values() if m["status"] == "healthy"]),
            "modules": [m for m in self.modules.keys()]
        }

# Global instance
registry = SystemRegistry()

def register_module(name: str = None, metadata: Dict[str, Any] = None):
    """Decorator to automatically register a class on initialization"""
    def decorator(cls):
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            original_init(self, *args, **kwargs)
            module_name = name or cls.__name__.lower()
            registry.register(module_name, self, metadata)
            
        cls.__init__ = new_init
        return cls
    return decorator

import os
import threading
from core.llm_exceptions import LLMClientUnavailableError

class LLMProvider:
    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.client = None
        self._init_client()

    def _init_client(self):
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            try:
                from groq import Groq
                self.client = Groq(api_key=api_key)
            except ImportError:
                self.client = None
        else:
            self.client = None

    @classmethod
    def instance(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = cls()
        return cls._instance

    def get_client(self):
        if not self.client:
            raise LLMClientUnavailableError(
                "LLM client not initialized. Set GROQ_API_KEY in .env"
            )
        return self.client
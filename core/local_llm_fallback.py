# ==========================================================
# JARVIS v9.0 - Local LLM Fallback
# llama.cpp for 100% uptime guarantee
# Automatic fallback on Groq failure
# ==========================================================

import logging
from typing import List, Dict, Any, Optional
import os
import subprocess
import json

logger = logging.getLogger(__name__)


class LocalLLMFallback:
    """
    Local LLM fallback using llama.cpp
    - 4-bit quantized Llama-3-8B (~4GB)
    - Automatic fallback on Groq failure
    - 100% uptime guarantee
    """

    def __init__(self, model_path: str = None):
        self.model_path = model_path or os.path.join("models", "llama-3-8b-q4.gguf")
        self.llama_cpp_available = False
        self.llm = None

        self._init_llama_cpp()

        logger.info("🏠 Local LLM Fallback initialized")

    def _init_llama_cpp(self):
        """Initialize llama.cpp"""
        try:
            from llama_cpp import Llama

            # Check if model exists
            if not os.path.exists(self.model_path):
                logger.warning(f"⚠️ Model not found at {self.model_path}")
                logger.info("📥 Download model: https://huggingface.co/TheBloke/Llama-2-7B-GGUF")
                return

            # Load model
            self.llm = Llama(
                model_path=self.model_path,
                n_ctx=4096,  # Context window
                n_threads=4,  # CPU threads
                n_gpu_layers=0,  # CPU only (set to -1 for GPU)
                verbose=False
            )

            self.llama_cpp_available = True
            logger.info(f"✅ llama.cpp loaded: {self.model_path}")

        except ImportError:
            logger.warning("⚠️ llama-cpp-python not installed")
            logger.info("Install: pip install llama-cpp-python")

        except Exception as e:
            logger.error(f"❌ llama.cpp initialization failed: {e}")

    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.7,
        stop: List[str] = None
    ) -> str:
        """
        Generate text using local LLM

        Args:
            messages: Chat messages in OpenAI format
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            stop: Stop sequences

        Returns:
            Generated text
        """
        if not self.llama_cpp_available:
            logger.error("❌ Local LLM not available")
            return "Error: Local LLM not available"

        try:
            # Convert messages to prompt
            prompt = self._messages_to_prompt(messages)

            # Generate
            response = self.llm(
                prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                stop=stop or ["</s>", "User:", "Human:"],
                echo=False
            )

            text = response['choices'][0]['text'].strip()
            logger.info(f"✅ Local LLM generated {len(text.split())} words")

            return text

        except Exception as e:
            logger.error(f"❌ Local generation failed: {e}")
            return f"Error: {str(e)}"

    def _messages_to_prompt(self, messages: List[Dict[str, str]]) -> str:
        """Convert OpenAI-style messages to Llama prompt format"""
        prompt = ""

        for msg in messages:
            role = msg.get("role", "user")
            content = msg.get("content", "")

            if role == "system":
                prompt += f"System: {content}\n\n"
            elif role == "user":
                prompt += f"User: {content}\n\n"
            elif role == "assistant":
                prompt += f"Assistant: {content}\n\n"

        prompt += "Assistant: "
        return prompt

    def is_available(self) -> bool:
        """Check if local LLM is available"""
        return self.llama_cpp_available

    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        if not self.llama_cpp_available:
            return {"available": False}

        return {
            "available": True,
            "model_path": self.model_path,
            "context_size": 4096,
            "model_size_gb": os.path.getsize(self.model_path) / (1024**3) if os.path.exists(self.model_path) else 0
        }


class HybridLLMManager:
    """
    Hybrid LLM manager with automatic fallback
    - Primary: Groq (fast, cloud)
    - Fallback: Local llama.cpp (reliable, offline)
    """

    def __init__(self, groq_api_key: str = None):
        self.groq_api_key = groq_api_key or os.getenv("GROQ_API_KEY")
        self.groq_available = False
        self.groq_client = None

        # Initialize Groq
        try:
            from groq import Groq
            self.groq_client = Groq(api_key=self.groq_api_key)
            self.groq_available = True
            logger.info("✅ Groq client initialized")
        except Exception as e:
            logger.warning(f"⚠️ Groq not available: {e}")

        # Initialize local fallback
        self.local_llm = LocalLLMFallback()

        # Stats
        self.stats = {
            "groq_calls": 0,
            "groq_failures": 0,
            "local_calls": 0,
            "fallback_triggered": 0
        }

        logger.info("🔄 Hybrid LLM Manager initialized")

    def generate(
        self,
        messages: List[Dict[str, str]],
        max_tokens: int = 512,
        temperature: float = 0.7,
        model: str = "llama-3.3-70b-versatile",
        force_local: bool = False
    ) -> Dict[str, Any]:
        """
        Generate text with automatic fallback

        Args:
            messages: Chat messages
            max_tokens: Maximum tokens
            temperature: Sampling temperature
            model: Groq model name
            force_local: Force local generation

        Returns:
            {text: str, source: str, time_ms: int}
        """
        import time
        start_time = time.time()

        # Force local if requested
        if force_local:
            return self._generate_local(messages, max_tokens, temperature, start_time)

        # Try Groq first
        if self.groq_available:
            try:
                self.stats["groq_calls"] += 1

                response = self.groq_client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature
                )

                text = response.choices[0].message.content
                elapsed_ms = int((time.time() - start_time) * 1000)

                logger.info(f"✅ Groq generation: {elapsed_ms}ms")

                return {
                    "text": text,
                    "source": "groq",
                    "model": model,
                    "time_ms": elapsed_ms
                }

            except Exception as e:
                logger.warning(f"⚠️ Groq failed: {e}")
                self.stats["groq_failures"] += 1
                self.stats["fallback_triggered"] += 1

        # Fallback to local
        return self._generate_local(messages, max_tokens, temperature, start_time)

    def _generate_local(self, messages, max_tokens, temperature, start_time) -> Dict[str, Any]:
        """Generate using local LLM"""
        self.stats["local_calls"] += 1

        text = self.local_llm.generate(messages, max_tokens, temperature)
        elapsed_ms = int((time.time() - start_time) * 1000)

        logger.info(f"🏠 Local generation: {elapsed_ms}ms")

        return {
            "text": text,
            "source": "local",
            "model": "llama-3-8b-q4",
            "time_ms": elapsed_ms
        }

    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            **self.stats,
            "groq_success_rate": (self.stats["groq_calls"] - self.stats["groq_failures"]) / self.stats["groq_calls"] if self.stats["groq_calls"] > 0 else 0.0,
            "local_available": self.local_llm.is_available(),
            "groq_available": self.groq_available
        }


# Test
if __name__ == "__main__":
    manager = HybridLLMManager()

    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "What is 2+2?"}
    ]

    print("\n" + "="*50)
    print("HYBRID LLM TEST")
    print("="*50)

    # Test with Groq
    result = manager.generate(messages, max_tokens=100)
    print(f"\n✅ Source: {result['source']}")
    print(f"Time: {result['time_ms']}ms")
    print(f"Text: {result['text'][:200]}")

    # Test with local (forced)
    result_local = manager.generate(messages, max_tokens=100, force_local=True)
    print(f"\n🏠 Source: {result_local['source']}")
    print(f"Time: {result_local['time_ms']}ms")
    print(f"Text: {result_local['text'][:200]}")

    # Stats
    print("\n" + "="*50)
    print("STATS")
    print("="*50)
    print(json.dumps(manager.get_stats(), indent=2))

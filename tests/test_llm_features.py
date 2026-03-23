import pytest
import asyncio
from core.llm_provider import LLMProvider
from core.speculative_decoder import SpeculativeDecoder

@pytest.mark.asyncio
async def test_llm_provider_fallback():
    provider = LLMProvider.instance()

    # Test generation (will use Groq if available, or fallback to Local)
    messages = [{"role": "user", "content": "echo 'test'"}]
    result = await provider.generate(messages, max_tokens=10)

    assert "text" in result
    assert "source" in result
    assert result["source"] in ["groq", "local"]

@pytest.mark.asyncio
async def test_speculative_decoder_adaptive():
    decoder = SpeculativeDecoder()

    # Test with adaptive draft length (None)
    messages = [{"role": "user", "content": "Explain gravity."}]
    # SpeculativeDecoder.generate is synchronous
    result = decoder.generate(messages, max_tokens=20, draft_length=None)

    assert "text" in result
    assert "tokens" in result
    assert "accepted_ratio" in result

    # Verify stats are updated
    stats = decoder.get_stats()
    assert stats["total_calls"] > 0

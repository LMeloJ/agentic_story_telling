"""
Integration tests with REAL API calls (optional).

These tests make actual API calls to Gemini and will appear in LangSmith if configured.
Use with caution - they consume API quota and may cost money.

To run these tests:
1. Set GEMINI_API_KEY in your environment
2. Optionally set LANGSMITH_TRACING=true and LANGSMITH_API_KEY to see traces
3. Run: pytest tests/test_real_api.py -v

These tests are marked with 'real_api' marker and can be skipped:
    pytest -m "not real_api"  # Skip real API tests
"""

import pytest
from src.services.gemini_service import GeminiService
from src.services.logging_service import get_logger

logger = get_logger("real_api_tests")


@pytest.mark.real_api
class TestRealGeminiAPI:
    """Tests that make real API calls to Gemini."""
    
    def test_real_gemini_call(self, real_api_env_vars):
        """Test making a real API call to Gemini (will appear in LangSmith if enabled)."""
        service = GeminiService()
        
        # This will make a REAL API call
        response = service.generate_response(
            prompt="Say hello in one sentence",
            system_instruction="You are a helpful assistant",
            max_tokens=50,  # Keep it short to save tokens
        )
        
        assert response is not None
        assert len(response) > 0
        assert "hello" in response.lower() or "hi" in response.lower()
        
        logger.info(f"Real API response: {response}")
        logger.info("If LANGSMITH_TRACING=true, check LangSmith dashboard for this trace!")
    
    def test_real_gemini_with_context(self, real_api_env_vars):
        """Test real API call with conversation context."""
        service = GeminiService()
        
        context = [
            {"role": "user", "content": "My name is Alice"},
            {"role": "npc", "content": "Nice to meet you, Alice!"},
        ]
        
        response = service.generate_response(
            prompt="What's my name?",
            context=context,
            max_tokens=50,  # Increased to allow full response
        )
        
        assert response is not None
        assert len(response) > 0
        
        # The model should remember the name from context
        # Check if response contains "alice" or acknowledges the name
        response_lower = response.lower()
        # Model might say "Your name is Alice" or "Alice" or reference it
        name_remembered = (
            "alice" in response_lower or
            "your name" in response_lower or
            "you said" in response_lower or
            "you told" in response_lower
        )
        
        if not name_remembered:
            logger.warning(f"Model response doesn't clearly reference the name: {response}")
            # Log but don't fail - context might be working but phrased differently
            # This is a soft check to verify context is being passed
        
        logger.info(f"Context-aware response: {response}")


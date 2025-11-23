"""
Gemini API service with retry logic, error handling, and circuit breaker.
"""

import time
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta

import google.generativeai as genai
from google.api_core import retry, exceptions

from src.config.config_loader import get_config
from src.services.logging_service import get_logger, LoggingService
from src.services.tracing_service import get_tracing_service, trace_api_call

logger = get_logger("gemini_service")
logging_service = LoggingService()
tracing_service = get_tracing_service()

# Import traceable decorator if LangSmith is available
try:
    from langsmith import traceable
except ImportError:
    # Create a no-op decorator if traceable is not available
    def traceable(*args, **kwargs):
        def decorator(func):
            return func
        return decorator


class CircuitBreaker:
    """Simple circuit breaker pattern implementation."""
    
    def __init__(self, failure_threshold: int = 5, timeout_seconds: int = 60):
        self.failure_threshold = failure_threshold
        self.timeout_seconds = timeout_seconds
        self.failure_count = 0
        self.last_failure_time: Optional[datetime] = None
        self.state = "closed"  # closed, open, half_open
    
    def record_success(self):
        """Record a successful call."""
        self.failure_count = 0
        self.state = "closed"
    
    def record_failure(self):
        """Record a failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.failure_count >= self.failure_threshold:
            self.state = "open"
            logger.warning(f"Circuit breaker opened after {self.failure_count} failures")
    
    def can_attempt(self) -> bool:
        """Check if a call can be attempted."""
        if self.state == "closed":
            return True
        
        if self.state == "open":
            if self.last_failure_time:
                elapsed = (datetime.now() - self.last_failure_time).total_seconds()
                if elapsed >= self.timeout_seconds:
                    self.state = "half_open"
                    logger.info("Circuit breaker entering half-open state")
                    return True
            return False
        
        # half_open state
        return True


class GeminiService:
    """Gemini API service with retry logic and circuit breaker."""
    
    def __init__(self):
        self.config = get_config()
        self.circuit_breaker = CircuitBreaker()
        self._client: Optional[genai.GenerativeModel] = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize Gemini client."""
        if self.config.development.mock_gemini:
            logger.info("Using mock Gemini service (MOCK_GEMINI=true)")
            return
        
        if not self.config.gemini.api_key:
            raise ValueError("GEMINI_API_KEY is required when MOCK_GEMINI is false")
        
        try:
            genai.configure(api_key=self.config.gemini.api_key)
            self._client = genai.GenerativeModel(self.config.gemini.model)
            logger.info(f"Initialized Gemini service with model: {self.config.gemini.model}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            raise
    
    def _exponential_backoff(self, attempt: int, base_delay: float = 1.0) -> float:
        """Calculate exponential backoff delay."""
        return base_delay * (2 ** attempt)
    
    @traceable(name="gemini.generate_response", run_type="llm")
    def generate_response(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        context: Optional[List[Dict[str, str]]] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ) -> str:
        """
        Generate a response using Gemini API with retry logic.
        
        Args:
            prompt: The main prompt for generation
            system_instruction: System instruction/personality prompt
            context: Conversation context (list of {"role": "user/npc", "content": "..."})
            temperature: Generation temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
        
        Returns:
            Generated response text
        
        Raises:
            Exception: If generation fails after all retries
        """
        start_time = time.time()
        
        # Check circuit breaker
        if not self.circuit_breaker.can_attempt():
            error_msg = "Circuit breaker is open - API calls temporarily disabled"
            logger.error(error_msg)
            raise Exception(error_msg)
        
        # Mock mode
        if self.config.development.mock_gemini or self._client is None:
            return self._mock_response(prompt, system_instruction)
        
        # Build generation config
        generation_config = {
            "temperature": temperature,
        }
        if max_tokens:
            generation_config["max_output_tokens"] = max_tokens
        
        # Build conversation history
        conversation_history = []
        if system_instruction:
            conversation_history.append({"role": "user", "parts": [system_instruction]})
            conversation_history.append({"role": "model", "parts": ["Understood."]})
        
        if context:
            for msg in context:
                role = "user" if msg.get("role") == "user" else "model"
                conversation_history.append({"role": role, "parts": [msg.get("content", "")]})
        
        conversation_history.append({"role": "user", "parts": [prompt]})
        
        # Retry logic
        last_exception = None
        for attempt in range(self.config.gemini.max_retries):
            try:
                # Generate response
                response = self._client.generate_content(
                    conversation_history,
                    generation_config=generation_config,
                )
                
                if response and response.text:
                    duration_ms = (time.time() - start_time) * 1000
                    self.circuit_breaker.record_success()
                    logging_service.log_api_call("gemini", "generate_content", duration_ms, success=True)
                    
                    # Trace API call
                    trace_api_call(
                        service_name="gemini",
                        operation="generate_content",
                        inputs={
                            "prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt,
                            "has_system_instruction": system_instruction is not None,
                            "context_length": len(context) if context else 0,
                            "temperature": temperature,
                        },
                        outputs={"response_length": len(response.text)},
                        metadata={
                            "model": self.config.gemini.model,
                            "circuit_breaker_state": self.circuit_breaker.state,
                        },
                        duration_ms=duration_ms,
                        success=True,
                    )
                    
                    return response.text.strip()
                else:
                    raise Exception("Empty response from Gemini API")
            
            except exceptions.ResourceExhausted as e:
                # Rate limit error
                last_exception = e
                if attempt < self.config.gemini.max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    logger.warning(f"Rate limit hit, retrying in {delay:.2f}s (attempt {attempt + 1}/{self.config.gemini.max_retries})")
                    time.sleep(delay)
                else:
                    duration_ms = (time.time() - start_time) * 1000
                    self.circuit_breaker.record_failure()
                    logging_service.log_api_call("gemini", "generate_content", duration_ms, success=False)
                    
                    # Trace failed API call
                    trace_api_call(
                        service_name="gemini",
                        operation="generate_content",
                        inputs={"prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt},
                        outputs=None,
                        metadata={"error": "Empty response from Gemini API"},
                        duration_ms=duration_ms,
                        success=False,
                    )
                    raise
            
            except Exception as e:
                last_exception = e
                if attempt < self.config.gemini.max_retries - 1:
                    delay = self._exponential_backoff(attempt)
                    logger.warning(f"API call failed, retrying in {delay:.2f}s (attempt {attempt + 1}/{self.config.gemini.max_retries}): {e}")
                    time.sleep(delay)
                else:
                    duration_ms = (time.time() - start_time) * 1000
                    self.circuit_breaker.record_failure()
                    logging_service.log_api_call("gemini", "generate_content", duration_ms, success=False)
                    
                    # Trace failed API call
                    trace_api_call(
                        service_name="gemini",
                        operation="generate_content",
                        inputs={"prompt": prompt[:100] + "..." if len(prompt) > 100 else prompt},
                        outputs=None,
                        metadata={"error": "Empty response from Gemini API"},
                        duration_ms=duration_ms,
                        success=False,
                    )
                    raise
        
        # Final failure
        self.circuit_breaker.record_failure()
        raise last_exception or Exception("Failed to generate response")
    
    def _mock_response(self, prompt: str, system_instruction: Optional[str] = None) -> str:
        """Generate a mock response for testing."""
        logger.debug(f"Mock Gemini response for prompt: {prompt[:50]}...")
        return f"[MOCK] Response to: {prompt[:100]}... (This is a mock response for testing)"
    
    def health_check(self) -> bool:
        """Check if Gemini service is healthy."""
        if self.config.development.mock_gemini:
            return True
        
        if not self.circuit_breaker.can_attempt():
            return False
        
        try:
            # Simple health check - generate a minimal response
            response = self.generate_response("Hello", max_tokens=10)
            return bool(response)
        except Exception as e:
            logger.warning(f"Gemini health check failed: {e}")
            return False


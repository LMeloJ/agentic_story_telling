"""
Tracing service for API call visualization using LangSmith.
"""

import os
from typing import Optional, Dict, Any, Callable
from functools import wraps
import time

from src.config.config_loader import get_config
from src.services.logging_service import get_logger

logger = get_logger("tracing_service")

# Try to import LangSmith, but make it optional
try:
    from langsmith import traceable, Client, RunTree
    from langsmith.run_helpers import tracing_context
    LANGSMITH_AVAILABLE = True
except ImportError:
    LANGSMITH_AVAILABLE = False
    traceable = None
    Client = None
    RunTree = None
    tracing_context = None


class TracingService:
    """Service for tracing API calls and operations with LangSmith."""
    
    _instance: Optional["TracingService"] = None
    _initialized: bool = False
    _enabled: bool = False
    _client: Optional[Any] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._initialize()
            TracingService._initialized = True
    
    def _initialize(self):
        """Initialize tracing service."""
        config = get_config()
        
        # Check if LangSmith is available
        if not LANGSMITH_AVAILABLE:
            logger.debug("LangSmith not available - tracing disabled")
            self._enabled = False
            return
        
        # Check if tracing is enabled via environment or config
        langsmith_tracing = os.getenv("LANGSMITH_TRACING", "false").lower() == "true"
        langsmith_api_key = os.getenv("LANGSMITH_API_KEY", "")
        
        if not langsmith_tracing or not langsmith_api_key:
            logger.debug("LangSmith tracing not enabled (set LANGSMITH_TRACING=true and LANGSMITH_API_KEY)")
            self._enabled = False
            return
        
        try:
            # Initialize LangSmith client
            self._client = Client(api_key=langsmith_api_key)
            self._enabled = True
            
            # Set environment variables for automatic tracing (LangChain/LangGraph integration)
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
            os.environ["LANGCHAIN_API_KEY"] = langsmith_api_key
            project_name = os.getenv("LANGSMITH_PROJECT", "dynevi")
            os.environ["LANGCHAIN_PROJECT"] = project_name
            
            logger.info(f"LangSmith tracing enabled - Project: {project_name}")
        except Exception as e:
            logger.warning(f"Failed to initialize LangSmith tracing: {e}")
            self._enabled = False
    
    def is_enabled(self) -> bool:
        """Check if tracing is enabled."""
        return self._enabled and LANGSMITH_AVAILABLE
    
    def trace_api_call(
        self,
        service_name: str,
        operation: str,
        inputs: Optional[Dict[str, Any]] = None,
        outputs: Optional[Any] = None,
        metadata: Optional[Dict[str, Any]] = None,
        duration_ms: Optional[float] = None,
        success: bool = True,
    ):
        """
        Trace an API call manually.
        
        Args:
            service_name: Name of the service (e.g., "gemini", "tts")
            operation: Operation name (e.g., "generate_content", "generate_audio")
            inputs: Input parameters
            outputs: Output/response
            metadata: Additional metadata
            duration_ms: Duration in milliseconds
            success: Whether the call was successful
        """
        if not self.is_enabled():
            return
        
        try:
            if self._client is None:
                return
            
            run_name = f"{service_name}.{operation}"
            run_type = "llm" if service_name == "gemini" else "tool"
            
            # Prepare metadata
            trace_metadata = metadata or {}
            if duration_ms is not None:
                trace_metadata["duration_ms"] = duration_ms
            
            # Create a run using LangSmith client
            try:
                from langsmith import RunTree
                
                # Create a run tree for this API call
                run = RunTree(
                    name=run_name,
                    run_type=run_type,
                    inputs=inputs or {},
                    outputs=outputs,
                    metadata=trace_metadata,
                    project_name=os.getenv("LANGSMITH_PROJECT", "dynevi"),
                )
                
                if not success:
                    run.error = "API call failed"
                
                # End the run (this sends it to LangSmith)
                run.end()
                
                logger.debug(f"Traced API call to LangSmith: {run_name} ({duration_ms}ms)")
            except ImportError:
                # RunTree might not be available in older versions
                logger.debug(f"LangSmith RunTree not available, using basic tracing")
                # Fall back to just logging
                logger.debug(f"Tracing API call: {run_name} ({duration_ms}ms)")
            
        except Exception as e:
            logger.warning(f"Failed to trace API call: {e}")
    
    def trace_function(
        self,
        name: Optional[str] = None,
        run_type: str = "function",
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """
        Decorator to trace a function.
        
        Usage:
            @tracing_service.trace_function(name="my_function")
            def my_function():
                ...
        """
        if not self.is_enabled() or traceable is None:
            # Return a no-op decorator if tracing is disabled
            def noop_decorator(func: Callable) -> Callable:
                return func
            return noop_decorator
        
        def decorator(func: Callable) -> Callable:
            func_name = name or func.__name__
            
            @traceable(name=func_name, run_type=run_type)
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    duration_ms = (time.time() - start_time) * 1000
                    
                    # Add metadata if provided
                    if metadata:
                        with tracing_context(metadata=metadata):
                            pass
                    
                    return result
                except Exception as e:
                    duration_ms = (time.time() - start_time) * 1000
                    logger.error(f"Error in traced function {func_name}: {e}")
                    raise
            
            return wrapper
        return decorator


# Global tracing service instance
_tracing_service: Optional[TracingService] = None


def get_tracing_service() -> TracingService:
    """Get the global tracing service instance."""
    global _tracing_service
    if _tracing_service is None:
        _tracing_service = TracingService()
    return _tracing_service


def trace_api_call(
    service_name: str,
    operation: str,
    inputs: Optional[Dict[str, Any]] = None,
    outputs: Optional[Any] = None,
    metadata: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[float] = None,
    success: bool = True,
):
    """
    Convenience function to trace an API call.
    
    Usage:
        trace_api_call("gemini", "generate_content", inputs={"prompt": "..."}, outputs=response, duration_ms=123.45)
    """
    service = get_tracing_service()
    service.trace_api_call(
        service_name=service_name,
        operation=operation,
        inputs=inputs,
        outputs=outputs,
        metadata=metadata,
        duration_ms=duration_ms,
        success=success,
    )


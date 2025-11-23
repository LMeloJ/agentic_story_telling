"""
Structured logging service for Dynevi system.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
from logging.handlers import RotatingFileHandler

from src.config.config_loader import get_config


class LoggingService:
    """Centralized logging service with structured logging and rotation."""
    
    _instance: Optional["LoggingService"] = None
    _initialized: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._setup_logging()
            LoggingService._initialized = True
    
    def _setup_logging(self):
        """Set up logging configuration."""
        config = get_config()
        
        # Create logs directory
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # Configure root logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, config.app.log_level))
        
        # Remove existing handlers
        root_logger.handlers.clear()
        
        # Console handler with formatting
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, config.app.log_level))
        console_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler)
        
        # File handler with rotation
        log_file = log_dir / f"dynevi_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(logging.DEBUG)  # Always log DEBUG to file
        file_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
        
        # Set specific logger levels
        logging.getLogger("chromadb").setLevel(logging.WARNING)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
    
    def log_conversation(self, npc_id: str, message: str, role: str = "npc"):
        """Log a conversation message."""
        logger = logging.getLogger("dynevi.conversation")
        logger.info(f"[{role.upper()}] {npc_id}: {message}")
    
    def log_memory_operation(self, operation: str, collection: str, details: str = ""):
        """Log a memory operation."""
        logger = logging.getLogger("dynevi.memory")
        logger.debug(f"Memory {operation} - Collection: {collection} - {details}")
    
    def log_api_call(self, service: str, endpoint: str, duration_ms: float, success: bool = True):
        """Log an API call with performance metrics."""
        logger = logging.getLogger("dynevi.api")
        status = "SUCCESS" if success else "FAILED"
        logger.info(f"API Call - {service}/{endpoint} - {status} - {duration_ms:.2f}ms")
    
    def log_error(self, component: str, error: Exception, context: dict = None):
        """Log an error with context."""
        logger = logging.getLogger(f"dynevi.{component}")
        context_str = f" - Context: {context}" if context else ""
        logger.error(f"Error in {component}: {str(error)}{context_str}", exc_info=True)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific component.
    
    Args:
        name: Logger name (typically module name)
    
    Returns:
        Logger instance
    """
    # Ensure logging service is initialized
    LoggingService()
    return logging.getLogger(f"dynevi.{name}")


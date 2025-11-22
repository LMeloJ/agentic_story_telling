"""
Centralized configuration loader with validation and hot-reload support.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
from dotenv import load_dotenv
from pydantic import BaseModel, Field, field_validator


class GeminiConfig(BaseModel):
    """Gemini API configuration."""
    api_key: str = Field(..., description="Google Gemini API key")
    model: str = Field(default="gemini-pro", description="Gemini model to use")
    timeout: int = Field(default=30, description="API timeout in seconds")
    max_retries: int = Field(default=3, description="Maximum retry attempts")


class TTSConfig(BaseModel):
    """Text-to-Speech configuration."""
    provider: str = Field(default="pyttsx3", description="TTS provider name")
    api_key: Optional[str] = Field(default=None, description="TTS API key (if required)")
    cache_dir: str = Field(default="./data/audio_cache", description="Audio cache directory")
    cache_max_size_mb: int = Field(default=500, description="Maximum cache size in MB")


class ChromaDBConfig(BaseModel):
    """ChromaDB configuration."""
    path: str = Field(default="./data/chroma_db", description="ChromaDB storage path")
    persist_directory: str = Field(default="./data/chroma_db", description="Persistent storage directory")


class AppConfig(BaseModel):
    """Application configuration."""
    environment: str = Field(default="development", description="Environment (development/production)")
    log_level: str = Field(default="INFO", description="Logging level")
    debug_mode: bool = Field(default=False, description="Enable debug mode")
    max_concurrent_requests: int = Field(default=5, description="Maximum concurrent API requests")
    api_timeout_seconds: int = Field(default=30, description="Default API timeout")
    memory_retrieval_limit: int = Field(default=10, description="Maximum memories to retrieve per query")

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of {valid_levels}")
        return v.upper()

    @field_validator("environment")
    @classmethod
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        valid_envs = ["development", "production", "testing"]
        if v.lower() not in valid_envs:
            raise ValueError(f"Environment must be one of {valid_envs}")
        return v.lower()


class DevelopmentConfig(BaseModel):
    """Development/testing configuration."""
    mock_gemini: bool = Field(default=False, description="Use mock Gemini API responses")
    mock_tts: bool = Field(default=False, description="Use mock TTS service")


class Config(BaseModel):
    """Main configuration model."""
    gemini: GeminiConfig
    tts: TTSConfig
    chromadb: ChromaDBConfig
    app: AppConfig
    development: DevelopmentConfig

    @classmethod
    def load_from_env(cls, env_file: Optional[str] = None) -> "Config":
        """
        Load configuration from environment variables.
        
        Args:
            env_file: Optional path to .env file. If None, searches for .env in project root.
        
        Returns:
            Config instance with loaded values.
        """
        if env_file is None:
            # Find project root (where .env.example or .env should be)
            project_root = Path(__file__).parent.parent.parent
            env_file = project_root / ".env"
        
        # Load environment variables
        if os.path.exists(env_file):
            load_dotenv(env_file)
        else:
            # Try loading from current directory
            load_dotenv()
        
        # Load configuration from environment
        return cls(
            gemini=GeminiConfig(
                api_key=os.getenv("GEMINI_API_KEY", ""),
                model=os.getenv("GEMINI_MODEL", "gemini-pro"),
                timeout=int(os.getenv("API_TIMEOUT_SECONDS", "30")),
                max_retries=int(os.getenv("GEMINI_MAX_RETRIES", "3")),
            ),
            tts=TTSConfig(
                provider=os.getenv("TTS_PROVIDER", "pyttsx3"),
                api_key=os.getenv("ELEVENLABS_API_KEY") or os.getenv("GOOGLE_CLOUD_TTS_KEY") or os.getenv("AZURE_SPEECH_KEY"),
                cache_dir=os.getenv("AUDIO_CACHE_DIR", "./data/audio_cache"),
                cache_max_size_mb=int(os.getenv("AUDIO_CACHE_MAX_SIZE_MB", "500")),
            ),
            chromadb=ChromaDBConfig(
                path=os.getenv("CHROMADB_PATH", "./data/chroma_db"),
                persist_directory=os.getenv("CHROMADB_PERSIST_DIRECTORY", "./data/chroma_db"),
            ),
            app=AppConfig(
                environment=os.getenv("ENVIRONMENT", "development"),
                log_level=os.getenv("LOG_LEVEL", "INFO"),
                debug_mode=os.getenv("DEBUG_MODE", "false").lower() == "true",
                max_concurrent_requests=int(os.getenv("MAX_CONCURRENT_REQUESTS", "5")),
                api_timeout_seconds=int(os.getenv("API_TIMEOUT_SECONDS", "30")),
                memory_retrieval_limit=int(os.getenv("MEMORY_RETRIEVAL_LIMIT", "10")),
            ),
            development=DevelopmentConfig(
                mock_gemini=os.getenv("MOCK_GEMINI", "false").lower() == "true",
                mock_tts=os.getenv("MOCK_TTS", "false").lower() == "true",
            ),
        )

    def validate(self) -> None:
        """Validate configuration and raise errors if invalid."""
        if not self.gemini.api_key and not self.development.mock_gemini:
            raise ValueError("GEMINI_API_KEY is required when MOCK_GEMINI is false")
        
        # Create directories if they don't exist
        Path(self.chromadb.path).mkdir(parents=True, exist_ok=True)
        Path(self.tts.cache_dir).mkdir(parents=True, exist_ok=True)


# Global configuration instance
_config: Optional[Config] = None


def get_config(reload: bool = False) -> Config:
    """
    Get global configuration instance.
    
    Args:
        reload: If True, reload configuration from environment.
    
    Returns:
        Config instance.
    """
    global _config
    if _config is None or reload:
        _config = Config.load_from_env()
        _config.validate()
    return _config


def reload_config() -> Config:
    """Reload configuration from environment."""
    return get_config(reload=True)


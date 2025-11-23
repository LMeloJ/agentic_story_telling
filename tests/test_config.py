"""
Tests for configuration system.
"""

import os
from pathlib import Path

import pytest

from src.config.config_loader import (
    Config,
    GeminiConfig,
    TTSConfig,
    ChromaDBConfig,
    AppConfig,
    DevelopmentConfig,
    get_config,
    reload_config,
)


class TestConfigModels:
    """Test configuration models."""
    
    def test_gemini_config(self):
        """Test GeminiConfig model."""
        config = GeminiConfig(
            api_key="test-key",
            model="gemini-2.5-flash",
            timeout=30,
            max_retries=3,
        )
        
        assert config.api_key == "test-key"
        assert config.model == "gemini-2.5-flash"
        assert config.timeout == 30
    
    def test_tts_config(self):
        """Test TTSConfig model."""
        config = TTSConfig(
            provider="pyttsx3",
            cache_dir="./test_cache",
        )
        
        assert config.provider == "pyttsx3"
        assert config.cache_dir == "./test_cache"
    
    def test_app_config_validation(self):
        """Test AppConfig validation."""
        # Valid log level
        config = AppConfig(log_level="INFO")
        assert config.log_level == "INFO"
        
        # Invalid log level should raise error
        with pytest.raises(Exception):
            AppConfig(log_level="INVALID")
        
        # Valid environment
        config = AppConfig(environment="development")
        assert config.environment == "development"
        
        # Invalid environment should raise error
        with pytest.raises(Exception):
            AppConfig(environment="invalid")


class TestConfigLoader:
    """Test configuration loading."""
    
    def test_load_config_from_env(self, mock_env_vars):
        """Test loading configuration from environment variables."""
        config = get_config(reload=True)
        
        assert config.gemini.api_key == "test-api-key-12345"
        assert config.gemini.model == "gemini-2.5-flash"
        assert config.development.mock_gemini is True
        assert config.development.mock_tts is True
        assert config.app.environment == "testing"
        assert config.app.log_level == "DEBUG"
    
    def test_config_validation(self, mock_env_vars):
        """Test configuration validation."""
        config = get_config(reload=True)
        
        # Should not raise exception for valid config
        config.validate()
        
        # Should create required directories
        assert Path(config.chromadb.path).exists() or Path(config.chromadb.path).parent.exists()
    
    def test_config_reload(self, mock_env_vars, monkeypatch):
        """Test configuration reloading."""
        config1 = get_config()
        
        # Change environment variable
        monkeypatch.setenv("LOG_LEVEL", "ERROR")
        
        # Reload config
        config2 = reload_config()
        
        assert config2.app.log_level == "ERROR"
    
    def test_config_defaults(self, mock_env_vars):
        """Test configuration defaults."""
        config = get_config(reload=True)
        
        # Check defaults are applied
        assert config.gemini.timeout == 30
        assert config.gemini.max_retries == 3
        assert config.tts.provider == "pyttsx3"
        assert config.app.max_concurrent_requests == 5
    
    def test_config_validation_without_api_key(self, monkeypatch, temp_dir):
        """Test config validation when API key is missing but mock is enabled."""
        # Set mock mode but no API key
        monkeypatch.setenv("MOCK_GEMINI", "true")
        monkeypatch.setenv("GEMINI_API_KEY", "")
        monkeypatch.setenv("MOCK_TTS", "true")
        monkeypatch.setenv("AUDIO_CACHE_DIR", str(temp_dir / "audio_cache"))
        monkeypatch.setenv("CHROMADB_PATH", str(temp_dir / "chromadb"))
        monkeypatch.setenv("ENVIRONMENT", "testing")
        
        config = get_config(reload=True)
        
        # Should not raise error when mock is enabled
        config.validate()
    
    def test_config_validation_requires_api_key(self, monkeypatch, temp_dir):
        """Test that API key is required when mock is disabled."""
        # Disable mock mode but no API key
        monkeypatch.setenv("MOCK_GEMINI", "false")
        monkeypatch.setenv("GEMINI_API_KEY", "")
        monkeypatch.setenv("MOCK_TTS", "true")
        monkeypatch.setenv("AUDIO_CACHE_DIR", str(temp_dir / "audio_cache"))
        monkeypatch.setenv("CHROMADB_PATH", str(temp_dir / "chromadb"))
        monkeypatch.setenv("ENVIRONMENT", "testing")
        
        # Should raise error during config loading (validation happens in get_config)
        with pytest.raises(ValueError, match="GEMINI_API_KEY is required"):
            get_config(reload=True)


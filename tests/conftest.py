"""
Pytest configuration and fixtures for Dynevi tests.
"""

import os
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from src.config.config_loader import Config, get_config, reload_config


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def mock_env_vars(monkeypatch, temp_dir: Path) -> Generator[dict, None, None]:
    """Set up mock environment variables for testing."""
    env_vars = {
        "GEMINI_API_KEY": "test-api-key-12345",
        "GEMINI_MODEL": "gemini-2.5-flash",
        "MOCK_GEMINI": "true",
        "MOCK_TTS": "true",
        "TTS_PROVIDER": "pyttsx3",
        "AUDIO_CACHE_DIR": str(temp_dir / "audio_cache"),
        "CHROMADB_PATH": str(temp_dir / "chromadb"),
        "CHROMADB_PERSIST_DIRECTORY": str(temp_dir / "chromadb"),
        "ENVIRONMENT": "testing",
        "LOG_LEVEL": "DEBUG",
    }
    
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    
    # Reload config to pick up new env vars
    reload_config()
    
    yield env_vars
    
    # Cleanup
    for key in env_vars.keys():
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def real_api_env_vars(monkeypatch, temp_dir: Path) -> Generator[dict, None, None]:
    """
    Set up environment variables for REAL API calls (use with caution!).
    
    This fixture disables mock mode, so tests will make actual API calls.
    Requires valid API keys in environment.
    """
    # Get real API key from environment (don't set a fake one)
    real_api_key = os.getenv("GEMINI_API_KEY", "")
    if not real_api_key:
        pytest.skip("GEMINI_API_KEY not set - skipping real API tests")
    
    env_vars = {
        "GEMINI_API_KEY": real_api_key,
        "GEMINI_MODEL": os.getenv("GEMINI_MODEL", "gemini-2.5-flash"),
        "MOCK_GEMINI": "false",  # Disable mock mode
        "MOCK_TTS": "true",  # Keep TTS mocked for speed
        "TTS_PROVIDER": "pyttsx3",
        "AUDIO_CACHE_DIR": str(temp_dir / "audio_cache"),
        "CHROMADB_PATH": str(temp_dir / "chromadb"),
        "CHROMADB_PERSIST_DIRECTORY": str(temp_dir / "chromadb"),
        "ENVIRONMENT": "testing",
        "LOG_LEVEL": "DEBUG",
        # Optional: Enable LangSmith tracing for real API tests
        "LANGSMITH_TRACING": os.getenv("LANGSMITH_TRACING", "false"),
        "LANGSMITH_API_KEY": os.getenv("LANGSMITH_API_KEY", ""),
        "LANGSMITH_PROJECT": os.getenv("LANGSMITH_PROJECT", "dynevi-tests"),
    }
    
    for key, value in env_vars.items():
        if value:  # Only set if value is not empty
            monkeypatch.setenv(key, value)
    
    # Reload config to pick up new env vars
    reload_config()
    
    yield env_vars
    
    # Cleanup
    for key in env_vars.keys():
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def test_config(mock_env_vars) -> Config:
    """Get test configuration."""
    return get_config(reload=True)


@pytest.fixture(autouse=True)
def reset_config():
    """Reset global config before each test."""
    reload_config()
    yield
    reload_config()

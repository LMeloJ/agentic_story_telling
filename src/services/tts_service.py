"""
Text-to-Speech service with caching and multiple provider support.
"""

import hashlib
import os
from pathlib import Path
from typing import Optional
import time

from src.config.config_loader import get_config
from src.services.logging_service import get_logger, LoggingService
from src.services.tracing_service import trace_api_call
from src.models.npc_profile import VoiceConfig

logger = get_logger("tts_service")
logging_service = LoggingService()


class TTSService:
    """Text-to-Speech service with caching and provider abstraction."""
    
    def __init__(self):
        self.config = get_config()
        self.cache_dir = Path(self.config.tts.cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self._provider = None
        self._initialize_provider()
    
    def _initialize_provider(self):
        """Initialize TTS provider based on configuration."""
        if self.config.development.mock_tts:
            logger.info("Using mock TTS service (MOCK_TTS=true)")
            self._provider = "mock"
            return
        
        provider_name = self.config.tts.provider.lower()
        
        if provider_name == "pyttsx3":
            try:
                import pyttsx3
                self._provider = pyttsx3.init()
                logger.info("Initialized pyttsx3 TTS provider")
            except Exception as e:
                logger.warning(f"Failed to initialize pyttsx3: {e}. Using mock provider.")
                self._provider = "mock"
        else:
            logger.warning(f"TTS provider '{provider_name}' not yet implemented. Using mock provider.")
            self._provider = "mock"
    
    def _get_cache_key(self, text: str, voice_config: VoiceConfig) -> str:
        """Generate cache key for text and voice configuration."""
        key_string = f"{text}|{voice_config.voice_id}|{voice_config.speed}|{voice_config.pitch}|{voice_config.accent}"
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _get_cached_file(self, cache_key: str) -> Optional[Path]:
        """Get cached audio file if it exists."""
        cache_file = self.cache_dir / f"{cache_key}.wav"
        if cache_file.exists():
            return cache_file
        return None
    
    def generate_audio(
        self,
        text: str,
        voice_config: VoiceConfig,
        output_path: Optional[Path] = None,
    ) -> Path:
        """
        Generate audio file from text with caching.
        
        Args:
            text: Text to convert to speech
            voice_config: Voice configuration for the NPC
            output_path: Optional output path (if not provided, uses cache)
        
        Returns:
            Path to generated audio file
        """
        start_time = time.time()
        
        # Check cache first
        cache_key = self._get_cache_key(text, voice_config)
        cached_file = self._get_cached_file(cache_key)
        if cached_file:
            logger.debug(f"Using cached audio file: {cached_file}")
            return cached_file
        
        # Generate new audio
        if output_path is None:
            output_path = self.cache_dir / f"{cache_key}.wav"
        
        if self._provider == "mock" or self.config.development.mock_tts:
            # Create empty file for mock
            output_path.touch()
            logger.debug(f"Mock TTS: Created placeholder file at {output_path}")
        else:
            # Use actual TTS provider
            self._generate_with_provider(text, voice_config, output_path)
        
        duration_ms = (time.time() - start_time) * 1000
        logging_service.log_api_call("tts", "generate_audio", duration_ms, success=True)
        
        # Trace API call
        trace_api_call(
            service_name="tts",
            operation="generate_audio",
            inputs={
                "text_length": len(text),
                "voice_id": voice_config.voice_id,
                "speed": voice_config.speed,
                "pitch": voice_config.pitch,
                "from_cache": cached_file is not None,
            },
            outputs={"audio_file": str(output_path)},
            metadata={
                "provider": self.config.tts.provider,
                "cache_hit": cached_file is not None,
            },
            duration_ms=duration_ms,
            success=True,
        )
        
        return output_path
    
    def _generate_with_provider(self, text: str, voice_config: VoiceConfig, output_path: Path):
        """Generate audio using the configured provider."""
        if isinstance(self._provider, str) and self._provider == "mock":
            output_path.touch()
            return
        
        try:
            import pyttsx3
            if isinstance(self._provider, pyttsx3.Engine):
                # Configure voice
                voices = self._provider.getProperty('voices')
                if voices and len(voices) > 0:
                    # Try to set voice by ID if available
                    try:
                        self._provider.setProperty('voice', voice_config.voice_id)
                    except:
                        pass  # Use default voice if ID not found
                
                self._provider.setProperty('rate', int(150 * voice_config.speed))  # Default rate is ~150
                self._provider.setProperty('volume', 1.0)
                
                # Save to file
                self._provider.save_to_file(text, str(output_path))
                self._provider.runAndWait()
                
                if not output_path.exists():
                    raise Exception("TTS file was not created")
        except Exception as e:
            logger.error(f"Failed to generate audio with provider: {e}")
            # Fallback to mock
            output_path.touch()
    
    def get_voice_config(self, npc_id: str) -> Optional[VoiceConfig]:
        """
        Get voice configuration for an NPC.
        
        Args:
            npc_id: NPC identifier
        
        Returns:
            VoiceConfig if found, None otherwise
        """
        # This would typically load from NPC profile
        # For now, return default
        return VoiceConfig()
    
    def clear_cache(self, max_age_days: int = 30):
        """Clear old cache files."""
        if not self.cache_dir.exists():
            return
        
        import time
        current_time = time.time()
        max_age_seconds = max_age_days * 24 * 60 * 60
        
        cleared_count = 0
        for cache_file in self.cache_dir.glob("*.wav"):
            file_age = current_time - cache_file.stat().st_mtime
            if file_age > max_age_seconds:
                cache_file.unlink()
                cleared_count += 1
        
        if cleared_count > 0:
            logger.info(f"Cleared {cleared_count} old cache files")


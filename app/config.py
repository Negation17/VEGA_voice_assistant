import os
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    """Application configuration loaded from environment or .env file."""
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # App Info
    APP_NAME: str = "VEGA AI Voice Assistant"
    VERSION: str = "0.1.0"

    # OpenAI & LLM
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    LLM_MODEL: str = os.getenv("LLM_MODEL", "gpt-4o-mini")
    SYSTEM_PROMPT: str = os.getenv(
        "SYSTEM_PROMPT",
        "You are VEGA, an intelligent, helpful, and concise AI voice assistant. "
        "Provide clear, direct, and conversational responses suitable for speech synthesis."
    )

    # Speech-to-Text (STT)
    STT_ENGINE: str = os.getenv("STT_ENGINE", "openai")  # openai, mock
    PCM_SAMPLE_RATE: int = int(os.getenv("PCM_SAMPLE_RATE", "16000"))
    PCM_CHANNELS: int = int(os.getenv("PCM_CHANNELS", "1"))
    PCM_SAMPLE_WIDTH: int = int(os.getenv("PCM_SAMPLE_WIDTH", "2"))  # 16-bit = 2 bytes
    SILENCE_THRESHOLD_RMS: float = float(os.getenv("SILENCE_THRESHOLD_RMS", "200.0"))

    # Text-to-Speech (TTS)
    TTS_ENGINE: str = os.getenv("TTS_ENGINE", "edge-tts")  # edge-tts, openai, mock
    TTS_VOICE: str = os.getenv("TTS_VOICE", "en-US-AriaNeural")

    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

settings = Settings()

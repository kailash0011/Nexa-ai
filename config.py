"""
Nexa AI — Configuration Loader
Reads settings from .env file using python-dotenv.
"""

import os
from pathlib import Path

from dotenv import load_dotenv

# Load .env file from project root
_env_path = Path(__file__).parent / ".env"
if not _env_path.exists():
    _env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=_env_path)


class Config:
    """Central configuration for Nexa AI."""

    # Owner / identity
    OWNER_NAME: str = os.getenv("OWNER_NAME", "Kailash")

    # Ollama / LLM settings
    OLLAMA_URL: str = os.getenv("OLLAMA_URL", "http://localhost:11434")
    OLLAMA_MODEL: str = os.getenv("OLLAMA_MODEL", "phi3")

    # Optional free API keys (fallback LLMs)
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")

    # Behaviour flags
    BUSY_MODE: bool = os.getenv("BUSY_MODE", "false").lower() == "true"
    VOICE_ENABLED: bool = os.getenv("VOICE_ENABLED", "true").lower() == "true"
    ADB_ENABLED: bool = os.getenv("ADB_ENABLED", "true").lower() == "true"

    # Voice settings
    VOICE_SPEED: int = int(os.getenv("VOICE_SPEED", "150"))
    VOICE_GENDER: str = os.getenv("VOICE_GENDER", "female")


# Singleton instance used throughout the project
config = Config()

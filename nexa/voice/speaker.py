"""
Nexa AI — Text-to-Speech (TTS)
Uses pyttsx3 for offline, free speech synthesis.
"""

import threading
from typing import Optional

from nexa.utils.logger import get_logger

logger = get_logger(__name__)

try:
    import pyttsx3  # type: ignore

    _PYTTSX3_AVAILABLE = True
except ImportError:
    _PYTTSX3_AVAILABLE = False
    logger.warning("⚠️  pyttsx3 not installed — TTS disabled. Run: pip install pyttsx3")


class Speaker:
    """
    Text-to-Speech engine for Nexa.
    Wraps pyttsx3 with configurable voice, speed, and volume.
    """

    def __init__(
        self,
        speed: int = 150,
        gender: str = "female",
        volume: float = 1.0,
    ) -> None:
        self.speed = speed
        self.gender = gender.lower()
        self.volume = volume
        self._engine: Optional[object] = None
        self._lock = threading.Lock()

        if _PYTTSX3_AVAILABLE:
            self._init_engine()

    def _init_engine(self) -> None:
        """Initialise the pyttsx3 engine and apply settings."""
        try:
            self._engine = pyttsx3.init()
            self._engine.setProperty("rate", self.speed)
            self._engine.setProperty("volume", self.volume)
            self._select_voice()
            logger.info("🔊 TTS engine initialised.")
        except Exception as exc:
            logger.error(f"TTS init error: {exc}")
            self._engine = None

    def _select_voice(self) -> None:
        """Select male or female voice if available."""
        if not self._engine:
            return
        voices = self._engine.getProperty("voices")
        for voice in voices:
            name = voice.name.lower()
            if self.gender == "female" and ("female" in name or "zira" in name or "hazel" in name):
                self._engine.setProperty("voice", voice.id)
                return
            if self.gender == "male" and ("male" in name or "david" in name or "george" in name):
                self._engine.setProperty("voice", voice.id)
                return

    def speak(self, text: str, blocking: bool = True) -> None:
        """
        Speak the given text aloud.

        Args:
            text: The text to synthesise and speak.
            blocking: If True (default), wait until speech finishes.
                      If False, speak in a background thread.
        """
        print(f"🤖 Nexa: {text}")

        if not _PYTTSX3_AVAILABLE or not self._engine:
            return

        if blocking:
            self._do_speak(text)
        else:
            t = threading.Thread(target=self._do_speak, args=(text,), daemon=True)
            t.start()

    def _do_speak(self, text: str) -> None:
        """Internal method — performs the actual synthesis."""
        with self._lock:
            try:
                self._engine.say(text)
                self._engine.runAndWait()
            except Exception as exc:
                logger.error(f"TTS speak error: {exc}")


# Module-level singleton — configured from config later
_speaker: Optional[Speaker] = None


def get_speaker(speed: int = 150, gender: str = "female") -> Speaker:
    """Return (and lazily create) the global Speaker instance."""
    global _speaker
    if _speaker is None:
        _speaker = Speaker(speed=speed, gender=gender)
    return _speaker

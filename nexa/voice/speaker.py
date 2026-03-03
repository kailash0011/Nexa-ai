"""
Nexa AI — Text-to-Speech (TTS)
Uses pyttsx3 for offline, free speech synthesis.
Reinitialises engine per utterance to work around Windows event-loop bugs.
"""

import platform
import subprocess
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

_IS_WINDOWS = platform.system() == "Windows"


class Speaker:
    """
    Text-to-Speech engine for Nexa.
    Creates a fresh pyttsx3 engine for every utterance to avoid
    the Windows bug where runAndWait() silently fails after first use.
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
        self._lock = threading.Lock()
        self._tts_available = _PYTTSX3_AVAILABLE

        # Quick smoke test — make sure pyttsx3 can init at all
        if self._tts_available:
            try:
                engine = pyttsx3.init()
                engine.stop()
                logger.info("🔊 TTS engine verified.")
            except Exception as exc:
                logger.error(f"TTS init test failed: {exc}")
                self._tts_available = False

    def _create_engine(self):
        """Create and configure a fresh pyttsx3 engine."""
        engine = pyttsx3.init()
        engine.setProperty("rate", self.speed)
        engine.setProperty("volume", self.volume)

        # Select voice by gender
        voices = engine.getProperty("voices")
        for voice in voices:
            name = voice.name.lower()
            if self.gender == "female" and ("female" in name or "zira" in name or "hazel" in name):
                engine.setProperty("voice", voice.id)
                break
            if self.gender == "male" and ("male" in name or "david" in name or "george" in name):
                engine.setProperty("voice", voice.id)
                break
        return engine

    def speak(self, text: str, blocking: bool = True) -> None:
        """
        Speak the given text aloud.

        Args:
            text: The text to synthesise and speak.
            blocking: If True (default), wait until speech finishes.
                      If False, speak in a background thread.
        """
        print(f"🤖 Nexa: {text}")

        if not self._tts_available:
            return

        if blocking:
            self._do_speak(text)
        else:
            t = threading.Thread(target=self._do_speak, args=(text,), daemon=True)
            t.start()

    def _do_speak(self, text: str) -> None:
        """Create a fresh engine, speak, and tear it down."""
        with self._lock:
            try:
                engine = self._create_engine()
                engine.say(text)
                engine.runAndWait()
                engine.stop()
            except Exception as exc:
                logger.warning(f"pyttsx3 error: {exc}. Trying fallback TTS...")
                self._fallback_speak(text)

    def _fallback_speak(self, text: str) -> None:
        """Fallback TTS using Windows SAPI via PowerShell."""
        if not _IS_WINDOWS:
            logger.error("Fallback TTS only available on Windows.")
            return
        try:
            # Pass text as $args[0] to avoid embedding it in the script string
            script = (
                "Add-Type -AssemblyName System.Speech; "
                "$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
                "$s.Speak($args[0])"
            )
            subprocess.run(
                ["powershell", "-Command", script, text],
                check=False,
            )
        except Exception as exc:
            logger.error(f"Fallback TTS error: {exc}")


# Module-level singleton — configured from config later
_speaker: Optional[Speaker] = None


def get_speaker(speed: int = 150, gender: str = "female") -> Speaker:
    """Return (and lazily create) the global Speaker instance."""
    global _speaker
    if _speaker is None:
        _speaker = Speaker(speed=speed, gender=gender)
    return _speaker
